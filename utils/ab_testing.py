"""
A/B Testing and Experimentation Framework
For testing different recommendation algorithms, UI variations, and features
"""

import json
import os
import hashlib
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from collections import defaultdict
import threading
from enum import Enum


class ExperimentStatus(Enum):
    DRAFT = 'draft'
    RUNNING = 'running'
    PAUSED = 'paused'
    COMPLETED = 'completed'
    ARCHIVED = 'archived'


class Variant:
    """Experiment variant definition"""

    def __init__(self, name: str, weight: float = 1.0,
                 config: Dict = None, description: str = ""):
        self.name = name
        self.weight = weight  # Traffic allocation weight
        self.config = config or {}
        self.description = description

        # Metrics tracking
        self.impressions = 0
        self.conversions = 0
        self.revenue = 0.0
        self.custom_metrics: Dict[str, float] = defaultdict(float)

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'weight': self.weight,
            'config': self.config,
            'description': self.description,
            'impressions': self.impressions,
            'conversions': self.conversions,
            'revenue': self.revenue,
            'custom_metrics': dict(self.custom_metrics),
            'conversion_rate': self.conversion_rate
        }

    @property
    def conversion_rate(self) -> float:
        if self.impressions == 0:
            return 0.0
        return round((self.conversions / self.impressions) * 100, 2)


class Experiment:
    """A/B Test experiment definition"""

    def __init__(self, experiment_id: str, name: str,
                 description: str = "", hypothesis: str = ""):
        self.experiment_id = experiment_id
        self.name = name
        self.description = description
        self.hypothesis = hypothesis

        self.status = ExperimentStatus.DRAFT
        self.variants: Dict[str, Variant] = {}
        self.control_variant: str = None

        # Targeting
        self.target_percentage = 100  # % of users to include
        self.user_segments: List[str] = []  # Specific user segments

        # Timing
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.ended_at: Optional[datetime] = None

        # Assignment tracking
        self.assignments: Dict[str, str] = {}  # user_id -> variant_name

        # Metrics configuration
        self.primary_metric = 'conversion_rate'
        self.secondary_metrics: List[str] = []

    def add_variant(self, variant: Variant, is_control: bool = False):
        """Add variant to experiment"""
        self.variants[variant.name] = variant
        if is_control:
            self.control_variant = variant.name

    def start(self):
        """Start the experiment"""
        if len(self.variants) < 2:
            raise ValueError("Experiment needs at least 2 variants")
        if not self.control_variant:
            # Set first variant as control if not specified
            self.control_variant = list(self.variants.keys())[0]

        self.status = ExperimentStatus.RUNNING
        self.started_at = datetime.now()

    def pause(self):
        """Pause the experiment"""
        self.status = ExperimentStatus.PAUSED

    def resume(self):
        """Resume the experiment"""
        self.status = ExperimentStatus.RUNNING

    def complete(self):
        """Complete the experiment"""
        self.status = ExperimentStatus.COMPLETED
        self.ended_at = datetime.now()

    def get_variant_for_user(self, user_id: str) -> Optional[Variant]:
        """Get assigned variant for user (or assign if new)"""
        if self.status != ExperimentStatus.RUNNING:
            return None

        # Check targeting
        if not self._is_user_targeted(user_id):
            return None

        # Check existing assignment
        if user_id in self.assignments:
            variant_name = self.assignments[user_id]
            return self.variants.get(variant_name)

        # Assign new user
        variant = self._assign_variant(user_id)
        return variant

    def _is_user_targeted(self, user_id: str) -> bool:
        """Check if user is in target group"""
        # Hash-based bucketing for consistent assignment
        hash_val = int(hashlib.md5(
            f"{self.experiment_id}:{user_id}".encode()
        ).hexdigest(), 16)

        bucket = hash_val % 100
        return bucket < self.target_percentage

    def _assign_variant(self, user_id: str) -> Variant:
        """Assign user to a variant based on weights"""
        # Calculate total weight
        total_weight = sum(v.weight for v in self.variants.values())

        # Hash for consistent assignment
        hash_val = int(hashlib.md5(
            f"{self.experiment_id}:variant:{user_id}".encode()
        ).hexdigest(), 16)

        # Normalize to 0-1 range
        rand_val = (hash_val % 10000) / 10000.0

        # Assign based on cumulative weights
        cumulative = 0.0
        for name, variant in self.variants.items():
            cumulative += variant.weight / total_weight
            if rand_val <= cumulative:
                self.assignments[user_id] = name
                variant.impressions += 1
                return variant

        # Fallback to last variant
        last_variant = list(self.variants.values())[-1]
        self.assignments[user_id] = last_variant.name
        last_variant.impressions += 1
        return last_variant

    def record_conversion(self, user_id: str, value: float = 1.0):
        """Record conversion for user's assigned variant"""
        if user_id not in self.assignments:
            return

        variant_name = self.assignments[user_id]
        if variant_name in self.variants:
            self.variants[variant_name].conversions += 1
            self.variants[variant_name].revenue += value

    def record_metric(self, user_id: str, metric_name: str, value: float):
        """Record custom metric for user's variant"""
        if user_id not in self.assignments:
            return

        variant_name = self.assignments[user_id]
        if variant_name in self.variants:
            self.variants[variant_name].custom_metrics[metric_name] += value

    def get_results(self) -> Dict:
        """Get experiment results"""
        results = {
            'experiment_id': self.experiment_id,
            'name': self.name,
            'status': self.status.value,
            'duration_days': self._get_duration_days(),
            'total_users': len(self.assignments),
            'variants': {},
            'winner': None,
            'statistical_significance': None
        }

        # Variant results
        control_cr = 0
        best_variant = None
        best_cr = 0

        for name, variant in self.variants.items():
            results['variants'][name] = variant.to_dict()
            results['variants'][name]['is_control'] = (name == self.control_variant)

            if name == self.control_variant:
                control_cr = variant.conversion_rate
            if variant.conversion_rate > best_cr:
                best_cr = variant.conversion_rate
                best_variant = name

        # Determine winner
        if best_variant and best_variant != self.control_variant:
            lift = ((best_cr - control_cr) / control_cr * 100) if control_cr > 0 else 0
            results['winner'] = {
                'variant': best_variant,
                'conversion_rate': best_cr,
                'lift_over_control': round(lift, 2)
            }

        return results

    def _get_duration_days(self) -> int:
        """Calculate experiment duration"""
        if not self.started_at:
            return 0
        end = self.ended_at or datetime.now()
        return (end - self.started_at).days

    def to_dict(self) -> Dict:
        return {
            'experiment_id': self.experiment_id,
            'name': self.name,
            'description': self.description,
            'hypothesis': self.hypothesis,
            'status': self.status.value,
            'variants': {k: v.to_dict() for k, v in self.variants.items()},
            'control_variant': self.control_variant,
            'target_percentage': self.target_percentage,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'total_assignments': len(self.assignments)
        }


class ABTestingManager:
    """
    A/B Testing and Experimentation Manager
    Handles multiple experiments and provides unified interface
    """

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(__file__), '..', 'data', 'experiments'
        )
        os.makedirs(self.storage_path, exist_ok=True)

        self.experiments: Dict[str, Experiment] = {}
        self.feature_flags: Dict[str, Dict] = {}
        self.lock = threading.Lock()

        # Load existing experiments
        self._load_experiments()

        print(f"  ABTestingManager initialized with {len(self.experiments)} experiments")

    def _load_experiments(self):
        """Load experiments from storage"""
        experiments_file = os.path.join(self.storage_path, 'experiments.json')
        if os.path.exists(experiments_file):
            try:
                with open(experiments_file, 'r') as f:
                    data = json.load(f)
                    # Load experiment data (simplified - full deserialization needed for production)
            except Exception as e:
                print(f"  Warning: Could not load experiments: {e}")

    def _save_experiments(self):
        """Save experiments to storage"""
        experiments_file = os.path.join(self.storage_path, 'experiments.json')
        data = {eid: exp.to_dict() for eid, exp in self.experiments.items()}
        with open(experiments_file, 'w') as f:
            json.dump(data, f, indent=2)

    # ==========================================
    # EXPERIMENT MANAGEMENT
    # ==========================================

    def create_experiment(self, name: str, description: str = "",
                         hypothesis: str = "") -> Experiment:
        """Create new experiment"""
        experiment_id = hashlib.md5(
            f"{name}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        experiment = Experiment(
            experiment_id=experiment_id,
            name=name,
            description=description,
            hypothesis=hypothesis
        )

        with self.lock:
            self.experiments[experiment_id] = experiment
            self._save_experiments()

        return experiment

    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Get experiment by ID"""
        return self.experiments.get(experiment_id)

    def list_experiments(self, status: ExperimentStatus = None) -> List[Dict]:
        """List all experiments"""
        experiments = []
        for exp in self.experiments.values():
            if status is None or exp.status == status:
                experiments.append(exp.to_dict())
        return experiments

    def start_experiment(self, experiment_id: str) -> bool:
        """Start an experiment"""
        exp = self.experiments.get(experiment_id)
        if exp:
            with self.lock:
                exp.start()
                self._save_experiments()
            return True
        return False

    def stop_experiment(self, experiment_id: str) -> bool:
        """Stop an experiment"""
        exp = self.experiments.get(experiment_id)
        if exp:
            with self.lock:
                exp.complete()
                self._save_experiments()
            return True
        return False

    # ==========================================
    # VARIANT ASSIGNMENT
    # ==========================================

    def get_variant(self, experiment_id: str, user_id: str) -> Optional[Dict]:
        """Get variant for user in experiment"""
        exp = self.experiments.get(experiment_id)
        if exp:
            variant = exp.get_variant_for_user(user_id)
            if variant:
                return {
                    'experiment_id': experiment_id,
                    'variant_name': variant.name,
                    'config': variant.config
                }
        return None

    def get_all_variants_for_user(self, user_id: str) -> Dict[str, Dict]:
        """Get all active experiment variants for user"""
        variants = {}
        for exp_id, exp in self.experiments.items():
            if exp.status == ExperimentStatus.RUNNING:
                variant = exp.get_variant_for_user(user_id)
                if variant:
                    variants[exp_id] = {
                        'experiment_name': exp.name,
                        'variant_name': variant.name,
                        'config': variant.config
                    }
        return variants

    # ==========================================
    # METRICS & CONVERSION TRACKING
    # ==========================================

    def track_conversion(self, experiment_id: str, user_id: str,
                        value: float = 1.0):
        """Track conversion event"""
        exp = self.experiments.get(experiment_id)
        if exp:
            with self.lock:
                exp.record_conversion(user_id, value)

    def track_metric(self, experiment_id: str, user_id: str,
                    metric_name: str, value: float):
        """Track custom metric"""
        exp = self.experiments.get(experiment_id)
        if exp:
            with self.lock:
                exp.record_metric(user_id, metric_name, value)

    def track_all_experiments(self, user_id: str, event_type: str,
                             value: float = 1.0):
        """Track event across all active experiments"""
        for exp_id, exp in self.experiments.items():
            if exp.status == ExperimentStatus.RUNNING:
                if user_id in exp.assignments:
                    if event_type == 'conversion':
                        exp.record_conversion(user_id, value)
                    else:
                        exp.record_metric(user_id, event_type, value)

    def get_results(self, experiment_id: str) -> Optional[Dict]:
        """Get experiment results"""
        exp = self.experiments.get(experiment_id)
        if exp:
            return exp.get_results()
        return None

    # ==========================================
    # FEATURE FLAGS
    # ==========================================

    def set_feature_flag(self, flag_name: str, enabled: bool,
                        percentage: int = 100, user_ids: List[str] = None):
        """Set feature flag configuration"""
        self.feature_flags[flag_name] = {
            'enabled': enabled,
            'percentage': percentage,
            'user_ids': user_ids or [],
            'updated_at': datetime.now().isoformat()
        }

    def is_feature_enabled(self, flag_name: str, user_id: str = None) -> bool:
        """Check if feature is enabled for user"""
        flag = self.feature_flags.get(flag_name)
        if not flag or not flag['enabled']:
            return False

        # Check specific user IDs
        if flag['user_ids'] and user_id:
            return user_id in flag['user_ids']

        # Percentage rollout
        if user_id and flag['percentage'] < 100:
            hash_val = int(hashlib.md5(
                f"{flag_name}:{user_id}".encode()
            ).hexdigest(), 16)
            return (hash_val % 100) < flag['percentage']

        return flag['enabled']

    def get_feature_flags(self) -> Dict:
        """Get all feature flags"""
        return self.feature_flags


# Pre-configured experiment templates
def create_recommendation_experiment(manager: ABTestingManager) -> Experiment:
    """Create recommendation algorithm A/B test"""
    exp = manager.create_experiment(
        name="Recommendation Algorithm Test",
        description="Testing different recommendation weights",
        hypothesis="Increasing content-based weight will improve conversion"
    )

    # Control: Current algorithm (60% CF, 40% CB)
    exp.add_variant(Variant(
        name="control",
        config={'cf_weight': 0.6, 'cb_weight': 0.4},
        description="Current algorithm"
    ), is_control=True)

    # Variant A: More content-based
    exp.add_variant(Variant(
        name="more_cb",
        config={'cf_weight': 0.4, 'cb_weight': 0.6},
        description="Higher content-based weight"
    ))

    # Variant B: Balanced
    exp.add_variant(Variant(
        name="balanced",
        config={'cf_weight': 0.5, 'cb_weight': 0.5},
        description="Equal weights"
    ))

    return exp


def create_chatbot_experiment(manager: ABTestingManager) -> Experiment:
    """Create chatbot backend A/B test"""
    exp = manager.create_experiment(
        name="Chatbot Backend Test",
        description="Testing LSTM vs Ollama chatbot",
        hypothesis="Ollama will provide better user satisfaction"
    )

    exp.add_variant(Variant(
        name="lstm",
        config={'backend': 'lstm'},
        description="LSTM neural network"
    ), is_control=True)

    exp.add_variant(Variant(
        name="ollama",
        config={'backend': 'ollama', 'model': 'llama3'},
        description="Ollama LLM"
    ))

    return exp


# Global instance
_ab_manager = None


def get_ab_manager(storage_path: str = None) -> ABTestingManager:
    """Get or create A/B testing manager instance"""
    global _ab_manager
    if _ab_manager is None:
        _ab_manager = ABTestingManager(storage_path)
    return _ab_manager


# For testing
if __name__ == "__main__":
    print("=" * 60)
    print("Testing A/B Testing Framework")
    print("=" * 60)

    manager = ABTestingManager()

    # Create experiment
    print("\n1. Creating recommendation experiment...")
    exp = create_recommendation_experiment(manager)
    print(f"   Created: {exp.name} ({exp.experiment_id})")

    # Add more variants and start
    print("\n2. Starting experiment...")
    manager.start_experiment(exp.experiment_id)

    # Simulate user assignments
    print("\n3. Simulating user assignments...")
    for i in range(100):
        user_id = f"USER_{i:03d}"
        variant = manager.get_variant(exp.experiment_id, user_id)
        if variant and random.random() < 0.15:  # 15% conversion rate
            manager.track_conversion(exp.experiment_id, user_id, value=100)

    # Get results
    print("\n4. Experiment Results:")
    results = manager.get_results(exp.experiment_id)
    print(f"   Total users: {results['total_users']}")
    for name, data in results['variants'].items():
        control_marker = " (CONTROL)" if data['is_control'] else ""
        print(f"   {name}{control_marker}:")
        print(f"     Impressions: {data['impressions']}")
        print(f"     Conversions: {data['conversions']}")
        print(f"     Conversion Rate: {data['conversion_rate']}%")

    if results['winner']:
        print(f"\n   Winner: {results['winner']['variant']}")
        print(f"   Lift over control: {results['winner']['lift_over_control']}%")

    # Test feature flags
    print("\n5. Testing Feature Flags...")
    manager.set_feature_flag('new_ui', True, percentage=50)
    for i in range(10):
        enabled = manager.is_feature_enabled('new_ui', f'USER_{i}')
        print(f"   USER_{i}: new_ui = {enabled}")

    print("\nTest complete!")

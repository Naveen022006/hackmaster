"""
API Routes for R7: Feedback Collection System
Handles feedback submission, retrieval, and analytics.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from services.feedback_service import get_feedback_service
from api.models import (
    FeedbackSubmitRequest,
    FeedbackResponse,
    FeedbackAnalyticsResponse,
    ProductFeedbackResponse,
    QualityMetricsResponse
)

router = APIRouter(prefix="/feedback", tags=["Feedback"])
feedback_service = get_feedback_service()


@router.post("/submit", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackSubmitRequest):
    """
    Submit user feedback on recommendations, products, or chat quality.
    
    - **user_id**: User identifier
    - **feedback_type**: Type of feedback (recommendation, product, chat_quality)
    - **rating**: Rating from 1-5
    - **target_id**: Product ID or recommendation ID
    - **comment**: Optional feedback comment
    """
    feedback = feedback_service.submit_feedback(
        user_id=request.user_id,
        feedback_type=request.feedback_type,
        rating=request.rating,
        target_id=request.target_id,
        comment=request.comment,
        metadata=request.metadata
    )

    return FeedbackResponse(
        id=feedback["id"],
        user_id=feedback["user_id"],
        type=feedback["type"],
        rating=feedback["rating"],
        target_id=feedback["target_id"],
        timestamp=feedback["timestamp"],
        message=f"Feedback received! Thank you for rating {request.feedback_type}."
    )


@router.get("/user/{user_id}")
async def get_user_feedback(user_id: str, feedback_type: Optional[str] = None):
    """
    Get all feedback submitted by a specific user.
    
    - **user_id**: User identifier
    - **feedback_type**: Optional filter by feedback type
    """
    feedbacks = feedback_service.get_feedback(user_id=user_id, feedback_type=feedback_type)

    return {
        "user_id": user_id,
        "total_feedback": len(feedbacks),
        "feedbacks": feedbacks,
        "filter": {"feedback_type": feedback_type} if feedback_type else None
    }


@router.get("/product/{product_id}", response_model=ProductFeedbackResponse)
async def get_product_feedback(product_id: str):
    """
    Get analytics for feedback on a specific product.
    
    - **product_id**: Product identifier
    """
    analytics = feedback_service.get_product_analytics(product_id)

    if analytics["total_feedback"] == 0:
        raise HTTPException(status_code=404, detail=f"No feedback found for product {product_id}")

    return ProductFeedbackResponse(**analytics)


@router.get("/analytics", response_model=FeedbackAnalyticsResponse)
async def get_feedback_analytics(feedback_type: Optional[str] = Query(None)):
    """
    Get overall feedback analytics and sentiment.
    
    - **feedback_type**: Optional filter by feedback type
    """
    analytics = feedback_service.get_analytics(feedback_type=feedback_type)

    return FeedbackAnalyticsResponse(
        total_feedback=analytics["total_feedback"],
        avg_rating=analytics["avg_rating"],
        sentiment=analytics["sentiment"],
        distribution=analytics["distribution"],
        recommendation_quality_score=None
    )


@router.get("/quality-metrics", response_model=QualityMetricsResponse)
async def get_quality_metrics():
    """
    Get recommendation quality metrics based on user feedback.
    Shows how well recommendations are rated by users.
    """
    metrics = feedback_service.get_quality_metrics()

    return QualityMetricsResponse(
        total_recommendations_rated=metrics["total_recommendations_rated"],
        avg_recommendation_rating=metrics["avg_recommendation_rating"],
        quality_score=metrics["quality_score"],
        distribution=metrics["distribution"]
    )


@router.post("/helpful/{feedback_id}")
async def mark_feedback_helpful(feedback_id: str):
    """
    Mark a feedback as helpful.
    
    - **feedback_id**: Feedback identifier
    """
    success = feedback_service.mark_feedback_helpful(feedback_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Feedback {feedback_id} not found")

    return {
        "success": True,
        "message": "Thank you for marking this feedback as helpful!",
        "feedback_id": feedback_id
    }


@router.get("/stats")
async def get_feedback_stats():
    """
    Get overall feedback statistics and summary.
    """
    all_feedback = feedback_service.get_feedback()

    feedback_by_type = {}
    for fb in all_feedback:
        fb_type = fb["type"]
        if fb_type not in feedback_by_type:
            feedback_by_type[fb_type] = []
        feedback_by_type[fb_type].append(fb)

    stats = {}
    for fb_type, feedbacks in feedback_by_type.items():
        ratings = [f["rating"] for f in feedbacks]
        stats[fb_type] = {
            "count": len(feedbacks),
            "avg_rating": sum(ratings) / len(ratings) if ratings else 0,
            "min_rating": min(ratings) if ratings else 0,
            "max_rating": max(ratings) if ratings else 0
        }

    return {
        "total_feedback": len(all_feedback),
        "feedback_by_type": stats,
        "unique_users": len(set(fb["user_id"] for fb in all_feedback))
    }

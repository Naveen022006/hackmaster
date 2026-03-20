/**
 * Personal Shopping Agent - Frontend Application
 * With User/Admin Authentication
 */

const API_BASE_URL = 'http://localhost:8000';

// State
let currentUser = null;
let authToken = null;
let isAdmin = false;
let currentView = 'chat';
let categories = [];
let brands = [];

// DOM Elements
const elements = {
    // Containers
    authContainer: document.getElementById('auth-container'),
    appContainer: document.getElementById('app-container'),

    // Auth Forms
    loginForm: document.getElementById('login-form'),
    registerForm: document.getElementById('register-form'),
    adminLoginForm: document.getElementById('admin-login-form'),

    // Auth switchers
    showRegister: document.getElementById('show-register'),
    showLogin: document.getElementById('show-login'),
    showAdminLogin: document.getElementById('show-admin-login'),
    backToUserLogin: document.getElementById('back-to-user-login'),

    // User info
    userInfo: document.getElementById('user-info'),
    currentUserName: document.getElementById('current-user-name'),
    currentUserEmail: document.getElementById('current-user-email'),
    logoutBtn: document.getElementById('logout-btn'),

    // Admin nav
    adminNav: document.getElementById('admin-nav'),

    // Navigation
    navItems: document.querySelectorAll('.nav-item'),
    views: document.querySelectorAll('.view'),
    statusDot: document.getElementById('status-dot'),
    statusText: document.getElementById('status-text'),

    // Chat
    chatMessages: document.getElementById('chat-messages'),
    chatForm: document.getElementById('chat-form'),
    chatInput: document.getElementById('chat-input'),
    quickQueries: document.querySelectorAll('.quick-query'),

    // Browse
    browseProducts: document.getElementById('browse-products'),
    filterCategory: document.getElementById('filter-category'),
    filterBrand: document.getElementById('filter-brand'),
    filterMaxPrice: document.getElementById('filter-max-price'),
    applyFiltersBtn: document.getElementById('apply-filters'),

    // Recommendations
    recProducts: document.getElementById('recommendation-products'),
    recFilters: document.querySelectorAll('.rec-filter'),

    // Profile
    profileUserId: document.getElementById('profile-user-id'),
    profileName: document.getElementById('profile-name'),
    profileEmail: document.getElementById('profile-email'),
    profileEngagement: document.getElementById('profile-engagement'),
    profileInteractions: document.getElementById('profile-interactions'),
    profileSpending: document.getElementById('profile-spending'),
    favoriteCategories: document.getElementById('favorite-categories'),
    favoriteBrands: document.getElementById('favorite-brands'),
    priceFill: document.getElementById('price-fill'),

    // Admin Dashboard
    statUsers: document.getElementById('stat-users'),
    statProducts: document.getElementById('stat-products'),
    statInteractions: document.getElementById('stat-interactions'),
    statCategories: document.getElementById('stat-categories'),
    seedDatabaseBtn: document.getElementById('seed-database-btn'),
    refreshStatsBtn: document.getElementById('refresh-stats-btn'),

    // Admin Tables
    usersTableBody: document.getElementById('users-table-body'),
    productsTableBody: document.getElementById('products-table-body'),

    // Modal
    modal: document.getElementById('product-modal'),
    modalBody: document.getElementById('modal-body'),
    modalClose: document.getElementById('modal-close'),

    // Toast
    toastContainer: document.getElementById('toast-container')
};

// ========================================
// Utility Functions
// ========================================

function formatPrice(price) {
    return '₹' + price.toLocaleString('en-IN');
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric'
    });
}

function getCategoryIcon(category) {
    const icons = {
        'Electronics': '📱',
        'Clothing': '👕',
        'Home & Kitchen': '🏠',
        'Books': '📚',
        'Beauty': '💄',
        'Sports': '⚽',
        'Toys': '🧸',
        'Grocery': '🛒'
    };
    return icons[category] || '📦';
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    elements.toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}

function showLoading(container) {
    container.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
        </div>
    `;
}

function showEmptyState(container, message) {
    container.innerHTML = `
        <div class="empty-state">
            <div class="empty-state-icon">🔍</div>
            <div class="empty-state-text">${message}</div>
        </div>
    `;
}

function getAuthHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }
    return headers;
}

// ========================================
// Local Storage Functions
// ========================================

function saveAuthState() {
    if (authToken) {
        localStorage.setItem('shopai_token', authToken);
        localStorage.setItem('shopai_user', JSON.stringify(currentUser));
    }
}

function loadAuthState() {
    const token = localStorage.getItem('shopai_token');
    const user = localStorage.getItem('shopai_user');
    if (token && user) {
        authToken = token;
        currentUser = JSON.parse(user);
        isAdmin = currentUser?.is_admin || false;
        return true;
    }
    return false;
}

function clearAuthState() {
    localStorage.removeItem('shopai_token');
    localStorage.removeItem('shopai_user');
    authToken = null;
    currentUser = null;
    isAdmin = false;
}

// ========================================
// API Functions
// ========================================

async function checkApiHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();

        if (data.status === 'healthy') {
            elements.statusDot.classList.add('online');
            elements.statusDot.classList.remove('offline');
            elements.statusText.textContent = 'API Connected';
            return true;
        }
    } catch (error) {
        elements.statusDot.classList.add('offline');
        elements.statusDot.classList.remove('online');
        elements.statusText.textContent = 'API Offline';
        return false;
    }
}

async function validateToken() {
    if (!authToken) return false;

    try {
        const response = await fetch(`${API_BASE_URL}/auth/validate`, {
            headers: getAuthHeaders()
        });
        const data = await response.json();
        return data.valid;
    } catch (error) {
        return false;
    }
}

async function loginUser(email, password) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Login failed');
        }

        return await response.json();
    } catch (error) {
        if (error.message.includes('fetch') || error.name === 'TypeError') {
            throw new Error('Cannot connect to API. Make sure the server is running (python -m uvicorn api.main:app --reload)');
        }
        throw error;
    }
}

async function loginAdmin(email, password) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/admin/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Admin login failed');
        }

        return await response.json();
    } catch (error) {
        if (error.message.includes('fetch') || error.name === 'TypeError') {
            throw new Error('Cannot connect to API. Make sure the server is running and MongoDB is connected.');
        }
        throw error;
    }
}

async function registerUser(name, email, password, phone, location) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password, phone, location })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Registration failed');
        }

        return await response.json();
    } catch (error) {
        if (error.message.includes('fetch') || error.name === 'TypeError') {
            throw new Error('Cannot connect to API. Make sure the server is running and MongoDB is connected.');
        }
        throw error;
    }
}

async function fetchCategories() {
    try {
        const response = await fetch(`${API_BASE_URL}/categories`);
        const data = await response.json();
        categories = data.categories;

        elements.filterCategory.innerHTML = '<option value="">All Categories</option>';
        categories.forEach(cat => {
            elements.filterCategory.innerHTML += `<option value="${cat}">${cat}</option>`;
        });
    } catch (error) {
        console.error('Error fetching categories:', error);
    }
}

async function fetchBrands(category = '') {
    try {
        const url = category
            ? `${API_BASE_URL}/brands?category=${encodeURIComponent(category)}`
            : `${API_BASE_URL}/brands`;
        const response = await fetch(url);
        const data = await response.json();
        brands = data.brands;

        elements.filterBrand.innerHTML = '<option value="">All Brands</option>';
        brands.forEach(brand => {
            elements.filterBrand.innerHTML += `<option value="${brand}">${brand}</option>`;
        });
    } catch (error) {
        console.error('Error fetching brands:', error);
    }
}

async function sendChatMessage(message) {
    const userId = currentUser?.user_id || 'guest';
    const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
            user_id: userId,
            message: message,
            top_n: 6
        })
    });
    return await response.json();
}

async function fetchProducts(filters = {}) {
    const params = new URLSearchParams();
    if (filters.category) params.append('category', filters.category);
    if (filters.brand) params.append('brand', filters.brand);
    if (filters.max_price) params.append('max_price', filters.max_price);
    params.append('limit', '50');

    const response = await fetch(`${API_BASE_URL}/products?${params}`);
    return await response.json();
}

async function fetchRecommendations(category = '') {
    const userId = currentUser?.user_id || 'U00001';
    const params = new URLSearchParams({
        user_id: userId,
        top_n: '20'
    });
    if (category) params.append('category', category);

    const response = await fetch(`${API_BASE_URL}/recommend?${params}`);
    return await response.json();
}

async function fetchUserProfile() {
    const userId = currentUser?.user_id || 'U00001';
    const response = await fetch(`${API_BASE_URL}/user/${userId}/profile`);
    return await response.json();
}

async function fetchSimilarProducts(productId) {
    const response = await fetch(`${API_BASE_URL}/products/${productId}/similar?top_n=6`);
    return await response.json();
}

async function recordInteraction(productId, action) {
    const userId = currentUser?.user_id || 'guest';
    const response = await fetch(`${API_BASE_URL}/interaction`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
            user_id: userId,
            product_id: productId,
            action: action
        })
    });
    return await response.json();
}

// Admin API Functions
async function fetchAdminStats() {
    const response = await fetch(`${API_BASE_URL}/admin/stats`, {
        headers: getAuthHeaders()
    });
    if (!response.ok) throw new Error('Failed to fetch stats');
    return await response.json();
}

async function fetchAdminUsers(page = 1) {
    const response = await fetch(`${API_BASE_URL}/admin/users?page=${page}&page_size=20`, {
        headers: getAuthHeaders()
    });
    if (!response.ok) throw new Error('Failed to fetch users');
    return await response.json();
}

async function fetchAdminProducts(page = 1) {
    const response = await fetch(`${API_BASE_URL}/admin/products?page=${page}&page_size=20`, {
        headers: getAuthHeaders()
    });
    if (!response.ok) throw new Error('Failed to fetch products');
    return await response.json();
}

async function toggleUserStatus(userId, isActive) {
    const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/status?is_active=${isActive}`, {
        method: 'PUT',
        headers: getAuthHeaders()
    });
    if (!response.ok) throw new Error('Failed to update user status');
    return await response.json();
}

async function seedDatabase() {
    const response = await fetch(`${API_BASE_URL}/admin/database/seed`, {
        method: 'POST',
        headers: getAuthHeaders()
    });
    if (!response.ok) throw new Error('Failed to seed database');
    return await response.json();
}

// ========================================
// UI Functions
// ========================================

function showAuthScreen() {
    elements.authContainer.classList.remove('hidden');
    elements.appContainer.classList.add('hidden');
}

function showAppScreen() {
    elements.authContainer.classList.add('hidden');
    elements.appContainer.classList.remove('hidden');
    updateUserUI();
}

function updateUserUI() {
    if (currentUser) {
        elements.currentUserName.textContent = currentUser.name || 'User';
        elements.currentUserEmail.textContent = currentUser.email || '';

        // Show/hide admin nav
        if (isAdmin) {
            elements.adminNav.classList.remove('hidden');
        } else {
            elements.adminNav.classList.add('hidden');
        }
    }
}

function switchAuthForm(form) {
    elements.loginForm.classList.add('hidden');
    elements.registerForm.classList.add('hidden');
    elements.adminLoginForm.classList.add('hidden');

    if (form === 'login') {
        elements.loginForm.classList.remove('hidden');
    } else if (form === 'register') {
        elements.registerForm.classList.remove('hidden');
    } else if (form === 'admin') {
        elements.adminLoginForm.classList.remove('hidden');
    }
}

// ========================================
// Render Functions
// ========================================

function renderProductCard(product, showActions = true) {
    const icon = getCategoryIcon(product.category);
    const rating = product.rating ? `⭐ ${product.rating.toFixed(1)}` : 'No rating';

    return `
        <div class="product-card" data-product-id="${product.product_id}">
            <div class="product-image">${icon}</div>
            <div class="product-info">
                <div class="product-category">${product.category}</div>
                <div class="product-name">${product.name}</div>
                <div class="product-brand">${product.brand}</div>
                <div class="product-footer">
                    <div class="product-price">${formatPrice(product.price)}</div>
                    <div class="product-rating">${rating}</div>
                </div>
            </div>
            ${showActions ? `
            <div class="product-actions">
                <button class="product-action-btn" onclick="handleProductAction(event, '${product.product_id}', 'view')">View</button>
                <button class="product-action-btn" onclick="handleProductAction(event, '${product.product_id}', 'add_to_cart')">Add to Cart</button>
                <button class="product-action-btn primary" onclick="handleProductAction(event, '${product.product_id}', 'purchase')">Buy</button>
            </div>
            ` : ''}
        </div>
    `;
}

function renderChatMessage(type, content, products = [], meta = {}) {
    const avatar = type === 'user' ? '👤' : '🤖';
    let productsHtml = '';

    if (products && products.length > 0) {
        productsHtml = `
            <div class="message-products">
                ${products.map(p => renderProductCard(p, true)).join('')}
            </div>
        `;
    }

    // Format content with basic markdown support
    let formattedContent = content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>')
        .replace(/^- /gm, '&bull; ');

    // Convert numbered lists
    formattedContent = formattedContent.replace(/^(\d+)\. /gm, '<span class="list-num">$1.</span> ');

    let metaHtml = '';
    if (meta.intent && meta.intent !== 'greeting' && meta.intent !== 'general') {
        const intentEmoji = {
            'search': '🔍',
            'buy': '🛒',
            'compare': '⚖️',
            'filter': '🎯',
            'recommendation': '✨',
            'help': '❓'
        };
        metaHtml = `
            <div class="message-meta">
                <span class="meta-intent">${intentEmoji[meta.intent] || '📋'} ${meta.intent}</span>
                <span class="meta-latency">⚡ ${meta.latency_ms?.toFixed(0)}ms</span>
                ${meta.cached ? '<span class="meta-cached">💾 cached</span>' : ''}
            </div>
        `;
    }

    // Add filters info if present
    let filtersHtml = '';
    if (meta.filters && Object.keys(meta.filters).length > 0) {
        const filterTags = [];
        if (meta.filters.category) filterTags.push(`📁 ${meta.filters.category}`);
        if (meta.filters.brand) filterTags.push(`🏷️ ${meta.filters.brand}`);
        if (meta.filters.max_price) filterTags.push(`💰 ≤₹${meta.filters.max_price.toLocaleString()}`);
        if (meta.filters.min_price) filterTags.push(`💰 ≥₹${meta.filters.min_price.toLocaleString()}`);
        if (meta.filters.min_rating) filterTags.push(`⭐ ${meta.filters.min_rating}+`);

        if (filterTags.length > 0) {
            filtersHtml = `
                <div class="message-filters">
                    ${filterTags.map(tag => `<span class="filter-tag">${tag}</span>`).join('')}
                </div>
            `;
        }
    }

    const messageHtml = `
        <div class="message ${type}">
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-text"><p>${formattedContent}</p></div>
                ${filtersHtml}
                ${productsHtml}
                ${metaHtml}
            </div>
        </div>
    `;

    elements.chatMessages.insertAdjacentHTML('beforeend', messageHtml);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;

    // Add click handlers to product cards
    const cards = elements.chatMessages.querySelectorAll('.product-card:not([data-bound])');
    cards.forEach(card => {
        card.setAttribute('data-bound', 'true');
        card.addEventListener('click', (e) => {
            if (!e.target.closest('.product-action-btn')) {
                const productId = card.dataset.productId;
                const product = products.find(p => p.product_id === productId);
                if (product) openProductModal(product);
            }
        });
    });
}

async function openProductModal(product) {
    const icon = getCategoryIcon(product.category);
    const rating = product.rating ? `⭐ ${product.rating.toFixed(1)}` : 'No rating';

    let similarHtml = '';
    try {
        const similarData = await fetchSimilarProducts(product.product_id);

        if (similarData.similar_products && similarData.similar_products.length > 0) {
            const priceAnalysis = similarData.price_analysis || {};
            const category = similarData.price_analysis.categories || {};

            // Build price analysis section
            let priceAnalysisHtml = `
                <div class="modal-price-analysis">
                    <h4>📊 Price Analysis</h4>
                    <div class="price-analysis-info">
                        <div class="analysis-item">
                            <span class="analysis-label">Original Price:</span>
                            <span class="analysis-value">${formatPrice(product.price)}</span>
                        </div>
                        <div class="analysis-item">
                            <span class="analysis-label">Price Range:</span>
                            <span class="analysis-value">${formatPrice(priceAnalysis.price_range.min)} - ${formatPrice(priceAnalysis.price_range.max)}</span>
                        </div>
                        <div class="analysis-item">
                            <span class="analysis-label">Cheaper Options:</span>
                            <span class="analysis-value">${category.cheaper_count || 0}</span>
                        </div>
                        <div class="analysis-item">
                            <span class="analysis-label">Similar Price:</span>
                            <span class="analysis-value">${category.similar_price_count || 0}</span>
                        </div>
                        <div class="analysis-item">
                            <span class="analysis-label">More Expensive:</span>
                            <span class="analysis-value">${category.expensive_count || 0}</span>
                        </div>
                    </div>
                </div>
            `;

            // Build similar products display
            let productsDisplay = similarData.similar_products.slice(0, 6).map((p, idx) => {
                const priceDiff = p.price - product.price;
                const priceDiffPercent = ((priceDiff / product.price) * 100).toFixed(0);
                let priceIndicator = '';

                if (priceDiff < 0) {
                    priceIndicator = `<span class="price-cheaper">💰 ${priceDiffPercent}% cheaper</span>`;
                } else if (priceDiff > 0) {
                    priceIndicator = `<span class="price-expensive">📈 ${priceDiffPercent}% expensive</span>`;
                } else {
                    priceIndicator = `<span class="price-similar">= Similar price</span>`;
                }

                return `
                    <div class="similar-product-card" onclick="handleSimilarProductClick('${p.product_id}')">
                        <div class="similar-product-header">
                            <div class="similar-product-icon">${getCategoryIcon(p.category)}</div>
                            <div class="similar-product-brand">${p.brand || 'Unknown'}</div>
                        </div>
                        <div class="similar-product-name" title="${p.name}">${p.name}</div>
                        <div class="similar-product-price">${formatPrice(p.price)}</div>
                        <div class="similar-product-indicator">${priceIndicator}</div>
                        ${p.rating ? `<div class="similar-product-rating">⭐ ${p.rating.toFixed(1)}</div>` : ''}
                    </div>
                `;
            }).join('');

            similarHtml = `
                <div class="modal-similar">
                    <h3>🔍 Similar Products [${similarData.original_category}]</h3>
                    ${priceAnalysisHtml}
                    <div class="similar-products-grid">
                        ${productsDisplay}
                    </div>
                    <div class="modal-similar-note">
                        Similar products are filtered by category and sorted by price comparison
                    </div>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error fetching similar products:', error);
    }

    elements.modalBody.innerHTML = `
        <div class="modal-product-header">
            <div class="modal-product-image">${icon}</div>
            <div class="modal-product-info">
                <h2>${product.name}</h2>
                <div class="category-brand">${product.category} • ${product.brand}</div>
                <div class="modal-price-rating">
                    <div class="modal-price">${formatPrice(product.price)}</div>
                    <div class="modal-rating">${rating}</div>
                </div>
            </div>
        </div>
        <div class="modal-description">
            ${product.description || 'No description available.'}
        </div>
        <div class="modal-actions">
            <button class="modal-action-btn view" onclick="handleModalAction('${product.product_id}', 'view')">
                👁️ View Details
            </button>
            <button class="modal-action-btn cart" onclick="handleModalAction('${product.product_id}', 'add_to_cart')">
                🛒 Add to Cart
            </button>
            <button class="modal-action-btn buy" onclick="handleModalAction('${product.product_id}', 'purchase')">
                💳 Buy Now
            </button>
        </div>
        ${similarHtml}
    `;

    elements.modal.classList.add('active');
    await recordInteraction(product.product_id, 'view');
}

// ========================================
// Event Handlers
// ========================================

function handleNavigation(view) {
    currentView = view;

    elements.navItems.forEach(item => {
        item.classList.toggle('active', item.dataset.view === view);
    });

    elements.views.forEach(v => {
        v.classList.toggle('active', v.id === `${view}-view`);
    });

    // Load view-specific data
    switch (view) {
        case 'browse':
            loadBrowseProducts();
            break;
        case 'recommendations':
            loadRecommendations();
            break;
        case 'profile':
            loadProfile();
            break;
        case 'admin-dashboard':
            loadAdminDashboard();
            break;
        case 'admin-users':
            loadAdminUsers();
            break;
        case 'admin-products':
            loadAdminProducts();
            break;
    }
}

async function handleChatSubmit(e) {
    e.preventDefault();
    const message = elements.chatInput.value.trim();
    if (!message) return;

    renderChatMessage('user', message);
    elements.chatInput.value = '';

    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'message bot loading-message';
    loadingMsg.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <div class="loading"><div class="spinner"></div></div>
            <span class="loading-text">Thinking...</span>
        </div>
    `;
    elements.chatMessages.appendChild(loadingMsg);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;

    try {
        const response = await sendChatMessage(message);
        loadingMsg.remove();
        renderChatMessage('bot', response.response, response.recommendations, {
            intent: response.intent,
            latency_ms: response.latency_ms,
            cached: response.cached,
            filters: response.filters_applied
        });
    } catch (error) {
        loadingMsg.remove();
        renderChatMessage('bot', "I'm having trouble connecting. Please make sure the server is running and try again.", [], {});
        showToast('Error processing your message', 'error');
    }
}

async function handleProductAction(e, productId, action) {
    e.stopPropagation();
    try {
        await recordInteraction(productId, action);
        const actionMessages = {
            'view': 'Viewing product details...',
            'add_to_cart': 'Added to cart!',
            'purchase': 'Thank you for your purchase!'
        };
        showToast(actionMessages[action], 'success');
    } catch (error) {
        showToast('Error recording action', 'error');
    }
}

async function handleModalAction(productId, action) {
    try {
        await recordInteraction(productId, action);
        const actionMessages = {
            'view': 'Product viewed',
            'add_to_cart': 'Added to cart!',
            'purchase': 'Thank you for your purchase!'
        };
        showToast(actionMessages[action], 'success');
        if (action === 'purchase') {
            elements.modal.classList.remove('active');
        }
    } catch (error) {
        showToast('Error processing action', 'error');
    }
}

async function handleSimilarProductClick(productId) {
    try {
        const products = await fetchProducts({});
        const product = products.products.find(p => p.product_id === productId);
        if (product) openProductModal(product);
    } catch (error) {
        console.error('Error loading product:', error);
    }
}

// ========================================
// Load Functions
// ========================================

async function loadBrowseProducts() {
    showLoading(elements.browseProducts);

    try {
        const filters = {
            category: elements.filterCategory.value,
            brand: elements.filterBrand.value,
            max_price: elements.filterMaxPrice.value
        };

        const data = await fetchProducts(filters);

        if (data.products && data.products.length > 0) {
            elements.browseProducts.innerHTML = data.products
                .map(p => renderProductCard(p))
                .join('');

            elements.browseProducts.querySelectorAll('.product-card').forEach(card => {
                card.addEventListener('click', (e) => {
                    if (!e.target.closest('.product-action-btn')) {
                        const productId = card.dataset.productId;
                        const product = data.products.find(p => p.product_id === productId);
                        if (product) openProductModal(product);
                    }
                });
            });
        } else {
            showEmptyState(elements.browseProducts, 'No products found');
        }
    } catch (error) {
        showEmptyState(elements.browseProducts, 'Error loading products');
    }
}

async function loadRecommendations(category = '') {
    showLoading(elements.recProducts);

    try {
        const data = await fetchRecommendations(category);

        if (data.recommendations && data.recommendations.length > 0) {
            elements.recProducts.innerHTML = data.recommendations
                .map(p => renderProductCard(p))
                .join('');

            elements.recProducts.querySelectorAll('.product-card').forEach(card => {
                card.addEventListener('click', (e) => {
                    if (!e.target.closest('.product-action-btn')) {
                        const productId = card.dataset.productId;
                        const product = data.recommendations.find(p => p.product_id === productId);
                        if (product) openProductModal(product);
                    }
                });
            });
        } else {
            showEmptyState(elements.recProducts, 'No recommendations available');
        }
    } catch (error) {
        showEmptyState(elements.recProducts, 'Error loading recommendations');
    }
}

async function loadProfile() {
    try {
        const profile = await fetchUserProfile();

        elements.profileUserId.textContent = currentUser?.user_id || profile.user_id;
        elements.profileName.textContent = currentUser?.name || '-';
        elements.profileEmail.textContent = currentUser?.email || '-';
        elements.profileEngagement.textContent = profile.engagement_score?.toFixed(1) || '0';
        elements.profileInteractions.textContent = profile.total_interactions || 0;
        elements.profileSpending.textContent = formatPrice(profile.avg_spending || 0);

        elements.favoriteCategories.innerHTML = profile.top_categories?.length
            ? profile.top_categories.map((cat, i) =>
                `<span class="tag ${i === 0 ? 'primary' : ''}">${getCategoryIcon(cat)} ${cat}</span>`
            ).join('')
            : '<span class="tag">No data yet</span>';

        elements.favoriteBrands.innerHTML = profile.top_brands?.length
            ? profile.top_brands.map((brand, i) =>
                `<span class="tag ${i === 0 ? 'primary' : ''}">${brand}</span>`
            ).join('')
            : '<span class="tag">No data yet</span>';

        const priceRange = profile.preferred_price_range || { min: 0, max: 100000 };
        const fillPercentage = Math.min(100, (priceRange.max / 100000) * 100);
        elements.priceFill.style.width = `${fillPercentage}%`;
    } catch (error) {
        showToast('Error loading profile', 'error');
    }
}

async function loadAdminDashboard() {
    try {
        const stats = await fetchAdminStats();
        elements.statUsers.textContent = stats.total_users.toLocaleString();
        elements.statProducts.textContent = stats.total_products.toLocaleString();
        elements.statInteractions.textContent = stats.total_interactions.toLocaleString();
        elements.statCategories.textContent = stats.categories.toLocaleString();
    } catch (error) {
        showToast('Error loading dashboard stats', 'error');
    }
}

async function loadAdminUsers(page = 1) {
    try {
        const data = await fetchAdminUsers(page);

        elements.usersTableBody.innerHTML = data.users.map(user => `
            <tr>
                <td>${user.user_id}</td>
                <td>${user.name || '-'}</td>
                <td>${user.email}</td>
                <td>${user.location || '-'}</td>
                <td>
                    <span class="status-badge ${user.is_active !== false ? 'active' : 'inactive'}">
                        ${user.is_active !== false ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td class="table-actions">
                    <button class="table-btn toggle" onclick="handleToggleUser('${user.user_id}', ${user.is_active === false})">
                        ${user.is_active !== false ? 'Deactivate' : 'Activate'}
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        showToast('Error loading users', 'error');
    }
}

async function loadAdminProducts(page = 1) {
    try {
        const data = await fetchAdminProducts(page);

        elements.productsTableBody.innerHTML = data.products.map(product => `
            <tr>
                <td>${product.product_id}</td>
                <td>${product.name}</td>
                <td>${product.category}</td>
                <td>${product.brand}</td>
                <td>${formatPrice(product.price)}</td>
                <td>${product.rating?.toFixed(1) || '-'}</td>
                <td class="table-actions">
                    <button class="table-btn edit" onclick="handleEditProduct('${product.product_id}')">Edit</button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        showToast('Error loading products', 'error');
    }
}

async function handleToggleUser(userId, newStatus) {
    try {
        await toggleUserStatus(userId, newStatus);
        showToast(`User ${newStatus ? 'activated' : 'deactivated'} successfully`, 'success');
        loadAdminUsers();
    } catch (error) {
        showToast('Error updating user status', 'error');
    }
}

function handleEditProduct(productId) {
    showToast('Edit functionality coming soon', 'info');
}

async function handleSeedDatabase() {
    if (!confirm('This will seed the database with sample data. Continue?')) return;

    showToast('Seeding database...', 'info');
    try {
        const result = await seedDatabase();
        showToast(`Database seeded: ${result.products_migrated} products, ${result.users_migrated} users`, 'success');
        loadAdminDashboard();
    } catch (error) {
        showToast('Error seeding database', 'error');
    }
}

// ========================================
// Auth Handlers
// ========================================

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    try {
        const data = await loginUser(email, password);
        authToken = data.access_token;
        currentUser = data.user;
        isAdmin = data.user.is_admin || false;
        saveAuthState();
        showToast('Login successful!', 'success');
        showAppScreen();
        fetchCategories();
        fetchBrands();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function handleAdminLogin(e) {
    e.preventDefault();
    const email = document.getElementById('admin-email').value;
    const password = document.getElementById('admin-password').value;

    try {
        const data = await loginAdmin(email, password);
        authToken = data.access_token;
        currentUser = data.user;
        isAdmin = true;
        saveAuthState();
        showToast('Admin login successful!', 'success');
        showAppScreen();
        fetchCategories();
        fetchBrands();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const name = document.getElementById('register-name').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const phone = document.getElementById('register-phone').value;
    const location = document.getElementById('register-location').value;

    try {
        const data = await registerUser(name, email, password, phone, location);
        authToken = data.access_token;
        currentUser = data.user;
        isAdmin = false;
        saveAuthState();
        showToast('Registration successful!', 'success');
        showAppScreen();
        fetchCategories();
        fetchBrands();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

function handleLogout() {
    clearAuthState();
    showToast('Logged out successfully', 'info');
    showAuthScreen();
    switchAuthForm('login');
}

// ========================================
// Initialize
// ========================================

async function init() {
    // Check API health
    await checkApiHealth();

    // Check for existing session
    if (loadAuthState()) {
        const isValid = await validateToken();
        if (isValid) {
            showAppScreen();
            fetchCategories();
            fetchBrands();
        } else {
            clearAuthState();
            showAuthScreen();
        }
    } else {
        showAuthScreen();
    }

    // Auth form switchers
    elements.showRegister?.addEventListener('click', (e) => {
        e.preventDefault();
        switchAuthForm('register');
    });

    elements.showLogin?.addEventListener('click', (e) => {
        e.preventDefault();
        switchAuthForm('login');
    });

    elements.showAdminLogin?.addEventListener('click', (e) => {
        e.preventDefault();
        switchAuthForm('admin');
    });

    elements.backToUserLogin?.addEventListener('click', (e) => {
        e.preventDefault();
        switchAuthForm('login');
    });

    // Auth form submissions
    elements.loginForm?.addEventListener('submit', handleLogin);
    elements.registerForm?.addEventListener('submit', handleRegister);
    elements.adminLoginForm?.addEventListener('submit', handleAdminLogin);
    elements.logoutBtn?.addEventListener('click', handleLogout);

    // Navigation handlers
    elements.navItems.forEach(item => {
        item.addEventListener('click', () => handleNavigation(item.dataset.view));
    });

    // Chat form
    elements.chatForm?.addEventListener('submit', handleChatSubmit);

    // Quick queries
    elements.quickQueries.forEach(btn => {
        btn.addEventListener('click', () => {
            elements.chatInput.value = btn.dataset.query;
            elements.chatForm.dispatchEvent(new Event('submit'));
        });
    });

    // Browse filters
    elements.filterCategory?.addEventListener('change', (e) => {
        fetchBrands(e.target.value);
    });

    elements.applyFiltersBtn?.addEventListener('click', loadBrowseProducts);

    // Recommendation filters
    elements.recFilters.forEach(btn => {
        btn.addEventListener('click', () => {
            elements.recFilters.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            loadRecommendations(btn.dataset.filter);
        });
    });

    // Admin buttons
    elements.seedDatabaseBtn?.addEventListener('click', handleSeedDatabase);
    elements.refreshStatsBtn?.addEventListener('click', loadAdminDashboard);

    // Modal close
    elements.modalClose?.addEventListener('click', () => {
        elements.modal.classList.remove('active');
    });

    elements.modal?.addEventListener('click', (e) => {
        if (e.target === elements.modal) {
            elements.modal.classList.remove('active');
        }
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && elements.modal.classList.contains('active')) {
            elements.modal.classList.remove('active');
        }
    });

    // Periodic health check
    setInterval(checkApiHealth, 30000);
}

// Start the app
document.addEventListener('DOMContentLoaded', init);

/**
 * AI Shopping Assistant - Frontend JavaScript
 * Handles chat interactions, product display, and user actions
 */

// ============================================
// Configuration
// ============================================
const API_BASE = '';  // Leave empty for same-origin
const USER_ID = 'GUEST_' + Math.random().toString(36).substr(2, 8);

// ============================================
// State Management
// ============================================
let currentSection = 'chat';
let cartItems = [];
let isTyping = false;

// ============================================
// DOM Elements
// ============================================
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const searchInput = document.getElementById('search-input');
const searchBtn = document.getElementById('search-btn');
const cartSidebar = document.getElementById('cart-sidebar');
const cartPreview = document.getElementById('cart-preview');
const closeCart = document.getElementById('close-cart');
const productModal = document.getElementById('product-modal');
const modalClose = document.getElementById('modal-close');

// ============================================
// Initialization
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initChatHandlers();
    initSearchHandlers();
    initCartHandlers();
    initModalHandlers();
    loadRecommendations();
    loadCategories();
    updateUserDisplay();
});

// ============================================
// Navigation
// ============================================
function initNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const section = item.dataset.section;
            switchSection(section);
        });
    });
}

function switchSection(section) {
    // Update nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.section === section);
    });

    // Update sections
    document.querySelectorAll('.content-section').forEach(sec => {
        sec.classList.remove('active');
    });
    document.getElementById(`${section}-section`).classList.add('active');

    currentSection = section;

    // Load section-specific content
    if (section === 'recommendations') {
        loadRecommendations();
    } else if (section === 'deals') {
        loadDeals();
    }
}

// ============================================
// Chat Handlers
// ============================================
function initChatHandlers() {
    // Send message on button click
    sendBtn.addEventListener('click', sendMessage);

    // Send message on Enter key
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Quick action buttons
    document.querySelectorAll('.quick-action').forEach(btn => {
        btn.addEventListener('click', () => {
            chatInput.value = btn.dataset.message;
            sendMessage();
        });
    });
}

async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message || isTyping) return;

    // Add user message to chat
    addMessage(message, 'user');
    chatInput.value = '';

    // Show typing indicator
    showTypingIndicator();

    try {
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, user_id: USER_ID })
        });

        const data = await response.json();
        hideTypingIndicator();

        if (data.success) {
            // Add bot response
            addBotMessage(data.response, data.products, data.action);

            // Update cart count if needed
            if (data.action === 'show_cart') {
                updateCartCount(data.products.length);
            }
        } else {
            addMessage('Sorry, I encountered an error. Please try again.', 'bot');
        }
    } catch (error) {
        hideTypingIndicator();
        addMessage('Unable to connect to the server. Please check your connection.', 'bot');
        console.error('Chat error:', error);
    }
}

function addMessage(content, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;

    const icon = type === 'user' ? 'fa-user' : 'fa-robot';

    messageDiv.innerHTML = `
        <div class="message-avatar">
            <i class="fas ${icon}"></i>
        </div>
        <div class="message-content">
            <p>${content}</p>
        </div>
    `;

    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addBotMessage(text, products, action) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';

    let productsHtml = '';
    if (products && products.length > 0) {
        productsHtml = `
            <div class="chat-products">
                ${products.map(p => createProductCardHTML(p)).join('')}
            </div>
        `;
    }

    messageDiv.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-robot"></i>
        </div>
        <div class="message-content">
            <p>${text}</p>
            ${productsHtml}
        </div>
    `;

    chatMessages.appendChild(messageDiv);

    // Add event listeners to product cards
    messageDiv.querySelectorAll('.product-card').forEach(card => {
        card.addEventListener('click', () => showProductModal(card.dataset.productId));
    });

    messageDiv.querySelectorAll('.add-cart-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            addToCart(btn.dataset.productId);
        });
    });

    messageDiv.querySelectorAll('.feedback-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            sendFeedback(btn.dataset.productId, btn.dataset.type);
        });
    });

    scrollToBottom();
}

function showTypingIndicator() {
    isTyping = true;
    const indicator = document.createElement('div');
    indicator.className = 'message bot-message typing-indicator';
    indicator.id = 'typing-indicator';
    indicator.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-robot"></i>
        </div>
        <div class="message-content">
            <div class="loading">
                <div class="loading-spinner"></div>
            </div>
        </div>
    `;
    chatMessages.appendChild(indicator);
    scrollToBottom();
}

function hideTypingIndicator() {
    isTyping = false;
    const indicator = document.getElementById('typing-indicator');
    if (indicator) indicator.remove();
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ============================================
// Search Handlers
// ============================================
function initSearchHandlers() {
    searchBtn.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') performSearch();
    });
}

async function performSearch() {
    const query = searchInput.value.trim();
    if (!query) return;

    switchSection('search');
    document.getElementById('search-query-display').textContent = `Results for "${query}"`;

    const grid = document.getElementById('search-results-grid');
    grid.innerHTML = '<div class="loading"><div class="loading-spinner"></div></div>';

    try {
        const response = await fetch(
            `${API_BASE}/api/products/search?q=${encodeURIComponent(query)}&user_id=${USER_ID}`
        );
        const data = await response.json();

        if (data.success && data.results.length > 0) {
            displayProducts(grid, data.results);
        } else {
            grid.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-search"></i>
                    <p>No products found for "${query}"</p>
                </div>
            `;
        }
    } catch (error) {
        grid.innerHTML = '<div class="empty-state"><p>Error loading results</p></div>';
        console.error('Search error:', error);
    }
}

// ============================================
// Product Display
// ============================================
function createProductCardHTML(product) {
    const discountBadge = product.discount_percent > 0
        ? `<div class="product-discount">-${product.discount_percent}%</div>`
        : '';

    const originalPrice = product.discount_percent > 0
        ? `<span class="original-price">$${product.price.toFixed(2)}</span>`
        : '';

    const finalPrice = product.price * (1 - product.discount_percent / 100);

    const icon = getCategoryIcon(product.category);

    return `
        <div class="product-card" data-product-id="${product.product_id}">
            <div class="product-image">
                <i class="fas ${icon}"></i>
                ${discountBadge}
            </div>
            <div class="product-info">
                <div class="product-category">${product.category}</div>
                <div class="product-name">${product.name}</div>
                <div class="product-rating">
                    <i class="fas fa-star"></i>
                    <span>${product.rating} (${product.num_reviews})</span>
                </div>
                <div class="product-price">
                    <span class="current-price">$${finalPrice.toFixed(2)}</span>
                    ${originalPrice}
                </div>
                <div class="product-actions">
                    <button class="add-cart-btn" data-product-id="${product.product_id}">
                        <i class="fas fa-cart-plus"></i> Add
                    </button>
                    <button class="feedback-btn" data-product-id="${product.product_id}" data-type="like">
                        <i class="fas fa-thumbs-up"></i>
                    </button>
                    <button class="feedback-btn dislike" data-product-id="${product.product_id}" data-type="dislike">
                        <i class="fas fa-thumbs-down"></i>
                    </button>
                </div>
            </div>
        </div>
    `;
}

function displayProducts(container, products) {
    container.innerHTML = products.map(p => createProductCardHTML(p)).join('');

    // Add event listeners
    container.querySelectorAll('.product-card').forEach(card => {
        card.addEventListener('click', (e) => {
            if (!e.target.closest('button')) {
                showProductModal(card.dataset.productId);
            }
        });
    });

    container.querySelectorAll('.add-cart-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            addToCart(btn.dataset.productId);
        });
    });

    container.querySelectorAll('.feedback-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            sendFeedback(btn.dataset.productId, btn.dataset.type);
        });
    });
}

function getCategoryIcon(category) {
    const icons = {
        'Electronics': 'fa-laptop',
        'Clothing': 'fa-tshirt',
        'Home & Kitchen': 'fa-couch',
        'Sports': 'fa-futbol',
        'Beauty': 'fa-spa',
        'Books': 'fa-book',
        'Toys': 'fa-gamepad',
        'Jewelry': 'fa-gem',
        'Automotive': 'fa-car',
        'Garden': 'fa-leaf'
    };
    return icons[category] || 'fa-box';
}

// ============================================
// Recommendations & Deals
// ============================================
async function loadRecommendations() {
    const grid = document.getElementById('recommendations-grid');
    grid.innerHTML = '<div class="loading"><div class="loading-spinner"></div></div>';

    try {
        const response = await fetch(`${API_BASE}/api/recommend`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: USER_ID, n: 12 })
        });
        const data = await response.json();

        if (data.success && data.recommendations.length > 0) {
            displayProducts(grid, data.recommendations);
        } else {
            grid.innerHTML = '<div class="empty-state"><p>No recommendations yet</p></div>';
        }
    } catch (error) {
        grid.innerHTML = '<div class="empty-state"><p>Error loading recommendations</p></div>';
        console.error('Recommendations error:', error);
    }
}

async function loadDeals() {
    const grid = document.getElementById('deals-grid');
    grid.innerHTML = '<div class="loading"><div class="loading-spinner"></div></div>';

    try {
        const response = await fetch(`${API_BASE}/api/recommend`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: USER_ID, n: 12 })
        });
        const data = await response.json();

        if (data.success) {
            // Filter for products with discounts
            const deals = data.recommendations.filter(p => p.discount_percent > 0);
            if (deals.length > 0) {
                displayProducts(grid, deals);
            } else {
                displayProducts(grid, data.recommendations.slice(0, 6));
            }
        }
    } catch (error) {
        grid.innerHTML = '<div class="empty-state"><p>Error loading deals</p></div>';
        console.error('Deals error:', error);
    }
}

// ============================================
// Categories
// ============================================
async function loadCategories() {
    const grid = document.getElementById('categories-grid');

    try {
        const response = await fetch(`${API_BASE}/api/categories`);
        const data = await response.json();

        if (data.success) {
            grid.innerHTML = data.categories.map(cat => `
                <div class="category-card" data-category="${cat}">
                    <i class="fas ${getCategoryIcon(cat)}"></i>
                    <h3>${cat}</h3>
                </div>
            `).join('');

            grid.querySelectorAll('.category-card').forEach(card => {
                card.addEventListener('click', () => loadCategoryProducts(card.dataset.category));
            });
        }
    } catch (error) {
        console.error('Categories error:', error);
    }
}

async function loadCategoryProducts(category) {
    const productsGrid = document.getElementById('category-products-grid');
    const categoriesGrid = document.getElementById('categories-grid');

    categoriesGrid.style.display = 'none';
    productsGrid.style.display = 'grid';
    productsGrid.innerHTML = '<div class="loading"><div class="loading-spinner"></div></div>';

    try {
        const response = await fetch(`${API_BASE}/api/recommend`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: USER_ID, n: 12, category: category })
        });
        const data = await response.json();

        if (data.success && data.recommendations.length > 0) {
            displayProducts(productsGrid, data.recommendations);
        } else {
            productsGrid.innerHTML = '<div class="empty-state"><p>No products in this category</p></div>';
        }

        // Add back button
        const backBtn = document.createElement('button');
        backBtn.className = 'quick-action';
        backBtn.innerHTML = '<i class="fas fa-arrow-left"></i> Back to Categories';
        backBtn.onclick = () => {
            categoriesGrid.style.display = 'grid';
            productsGrid.style.display = 'none';
        };
        productsGrid.insertBefore(backBtn, productsGrid.firstChild);

    } catch (error) {
        productsGrid.innerHTML = '<div class="empty-state"><p>Error loading products</p></div>';
        console.error('Category products error:', error);
    }
}

// ============================================
// Cart Handlers
// ============================================
function initCartHandlers() {
    cartPreview.addEventListener('click', toggleCart);
    closeCart.addEventListener('click', toggleCart);

    // Close cart on outside click
    document.addEventListener('click', (e) => {
        if (cartSidebar.classList.contains('open') &&
            !cartSidebar.contains(e.target) &&
            !cartPreview.contains(e.target)) {
            cartSidebar.classList.remove('open');
        }
    });
}

function toggleCart() {
    cartSidebar.classList.toggle('open');
    if (cartSidebar.classList.contains('open')) {
        loadCart();
    }
}

async function loadCart() {
    const cartItemsContainer = document.getElementById('cart-items');
    cartItemsContainer.innerHTML = '<div class="loading"><div class="loading-spinner"></div></div>';

    try {
        const response = await fetch(`${API_BASE}/api/cart?user_id=${USER_ID}`);
        const data = await response.json();

        if (data.success) {
            cartItems = data.cart;
            updateCartCount(data.cart_count);
            document.getElementById('cart-total').textContent = `$${data.total.toFixed(2)}`;

            if (data.cart.length > 0) {
                cartItemsContainer.innerHTML = data.cart.map(item => `
                    <div class="cart-item">
                        <div class="cart-item-image">
                            <i class="fas ${getCategoryIcon(item.category)}"></i>
                        </div>
                        <div class="cart-item-info">
                            <div class="cart-item-name">${item.name}</div>
                            <div class="cart-item-price">$${(item.price * (1 - item.discount_percent/100)).toFixed(2)}</div>
                        </div>
                        <button class="cart-item-remove" data-product-id="${item.product_id}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                `).join('');

                cartItemsContainer.querySelectorAll('.cart-item-remove').forEach(btn => {
                    btn.addEventListener('click', () => removeFromCart(btn.dataset.productId));
                });
            } else {
                cartItemsContainer.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-shopping-cart"></i>
                        <p>Your cart is empty</p>
                    </div>
                `;
            }
        }
    } catch (error) {
        cartItemsContainer.innerHTML = '<div class="empty-state"><p>Error loading cart</p></div>';
        console.error('Cart error:', error);
    }
}

async function addToCart(productId) {
    try {
        const response = await fetch(`${API_BASE}/api/cart/add`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: USER_ID, product_id: productId })
        });
        const data = await response.json();

        if (data.success) {
            updateCartCount(data.cart_count);
            showNotification('Added to cart!', 'success');

            // Track click
            trackClick(productId);
        }
    } catch (error) {
        showNotification('Error adding to cart', 'error');
        console.error('Add to cart error:', error);
    }
}

async function removeFromCart(productId) {
    try {
        const response = await fetch(`${API_BASE}/api/cart/remove`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: USER_ID, product_id: productId })
        });
        const data = await response.json();

        if (data.success) {
            updateCartCount(data.cart_count);
            loadCart();
            showNotification('Removed from cart', 'info');
        }
    } catch (error) {
        showNotification('Error removing from cart', 'error');
        console.error('Remove from cart error:', error);
    }
}

function updateCartCount(count) {
    document.getElementById('cart-count').textContent = count;
}

// ============================================
// Product Modal
// ============================================
function initModalHandlers() {
    modalClose.addEventListener('click', closeModal);
    productModal.addEventListener('click', (e) => {
        if (e.target === productModal) closeModal();
    });
}

async function showProductModal(productId) {
    productModal.classList.add('open');
    const modalBody = document.getElementById('modal-body');
    modalBody.innerHTML = '<div class="loading"><div class="loading-spinner"></div></div>';

    try {
        const response = await fetch(`${API_BASE}/api/product/${productId}?user_id=${USER_ID}`);
        const data = await response.json();

        if (data.success) {
            const p = data.product;
            const finalPrice = p.price * (1 - p.discount_percent / 100);

            modalBody.innerHTML = `
                <div class="modal-product">
                    <div class="modal-image">
                        <i class="fas ${getCategoryIcon(p.category)}"></i>
                    </div>
                    <div class="modal-info">
                        <h2>${p.name}</h2>
                        <div class="modal-category">${p.category} > ${p.subcategory}</div>
                        <div class="product-rating">
                            <i class="fas fa-star"></i>
                            <span>${p.rating} (${p.num_reviews} reviews)</span>
                        </div>
                        <p class="modal-description">${p.description}</p>
                        <div class="modal-price">$${finalPrice.toFixed(2)}</div>
                        ${p.discount_percent > 0 ? `<p style="color: var(--danger-color);">Save ${p.discount_percent}%!</p>` : ''}
                        <div class="modal-actions">
                            <button class="modal-add-cart" data-product-id="${p.product_id}">
                                <i class="fas fa-cart-plus"></i> Add to Cart
                            </button>
                            <button class="modal-like" data-product-id="${p.product_id}" data-type="like">
                                <i class="fas fa-thumbs-up"></i>
                            </button>
                            <button class="modal-dislike" data-product-id="${p.product_id}" data-type="dislike">
                                <i class="fas fa-thumbs-down"></i>
                            </button>
                        </div>
                    </div>
                </div>
                ${data.similar_products.length > 0 ? `
                    <div class="similar-products">
                        <h3>Similar Products</h3>
                        <div class="similar-grid">
                            ${data.similar_products.map(sp => `
                                <div class="similar-item" data-product-id="${sp.product_id}">
                                    <i class="fas ${getCategoryIcon(sp.category)}"></i>
                                    <span>${sp.name.substring(0, 30)}...</span>
                                    <span>$${(sp.price * (1 - sp.discount_percent/100)).toFixed(2)}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            `;

            // Add event listeners
            modalBody.querySelector('.modal-add-cart').addEventListener('click', (e) => {
                addToCart(e.target.closest('button').dataset.productId);
            });

            modalBody.querySelectorAll('.modal-like, .modal-dislike').forEach(btn => {
                btn.addEventListener('click', () => {
                    sendFeedback(btn.dataset.productId, btn.dataset.type);
                });
            });

            modalBody.querySelectorAll('.similar-item').forEach(item => {
                item.addEventListener('click', () => {
                    showProductModal(item.dataset.productId);
                });
            });

            // Track click
            trackClick(productId);
        }
    } catch (error) {
        modalBody.innerHTML = '<div class="empty-state"><p>Error loading product</p></div>';
        console.error('Product modal error:', error);
    }
}

function closeModal() {
    productModal.classList.remove('open');
}

// ============================================
// Feedback & Tracking
// ============================================
async function sendFeedback(productId, feedbackType) {
    try {
        const response = await fetch(`${API_BASE}/api/feedback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: USER_ID,
                product_id: productId,
                feedback_type: feedbackType
            })
        });
        const data = await response.json();

        if (data.success) {
            showNotification(
                feedbackType === 'like' ? 'Thanks for your feedback!' : 'Got it, we\'ll show less of this',
                feedbackType === 'like' ? 'success' : 'info'
            );
        }
    } catch (error) {
        console.error('Feedback error:', error);
    }
}

async function trackClick(productId) {
    try {
        await fetch(`${API_BASE}/api/click`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: USER_ID, product_id: productId })
        });
    } catch (error) {
        console.error('Track click error:', error);
    }
}

// ============================================
// Utility Functions
// ============================================
function updateUserDisplay() {
    document.getElementById('user-id-display').textContent = `User: ${USER_ID}`;
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#6366f1'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add CSS animations for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

/**
 * YAHOO NEWS AI CRAWLER - API CLIENT
 * ===================================
 *
 * JavaScript client để kết nối Dashboard với Flask Backend
 * Sử dụng REST API + WebSocket cho real-time updates
 *
 * Author: Claude Code + User
 */

// API Configuration
const API_CONFIG = {
    baseURL: 'http://localhost:5000',
    timeout: 30000  // 30 seconds
};

// WebSocket connection
let socket = null;
let isSocketConnected = false;

// =========================
// WEBSOCKET FUNCTIONS
// =========================

/**
 * Khởi tạo WebSocket connection
 */
function initWebSocket() {
    try {
        socket = io(API_CONFIG.baseURL);

        socket.on('connect', () => {
            console.log('✓ WebSocket connected');
            isSocketConnected = true;
            updateConnectionStatus(true);
        });

        socket.on('disconnect', () => {
            console.log('✗ WebSocket disconnected');
            isSocketConnected = false;
            updateConnectionStatus(false);
        });

        // Crawler logs
        socket.on('crawler_log', (data) => {
            console.log('[Crawler]', data.message);
            addCrawlerLog(data.message, data.timestamp);
        });

        // Crawler status changes
        socket.on('crawler_status', (data) => {
            updateCrawlerStatus(data.running);
        });

        // Articles update
        socket.on('articles_update', (data) => {
            console.log('Articles updated:', data);
            refreshArticles();
        });

    } catch (error) {
        console.error('WebSocket init error:', error);
        isSocketConnected = false;
    }
}

/**
 * Request data update via WebSocket
 */
function requestUpdate() {
    if (socket && isSocketConnected) {
        socket.emit('request_update');
    }
}

// =========================
// API FUNCTIONS
// =========================

/**
 * Generic API call helper
 */
async function apiCall(endpoint, options = {}) {
    const url = `${API_CONFIG.baseURL}${endpoint}`;

    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json'
        }
    };

    const finalOptions = { ...defaultOptions, ...options };

    try {
        const response = await fetch(url, finalOptions);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        // Check if response is JSON or file download
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        } else {
            return response;  // Return raw response for file downloads
        }
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        throw error;
    }
}

/**
 * Health check
 */
async function checkHealth() {
    return await apiCall('/api/health');
}

/**
 * Load articles với filters
 * @param {Object} params - Query parameters
 * @returns {Promise<Object>} Articles data với pagination
 */
async function loadArticles(params = {}) {
    const {
        page = 1,
        limit = 10,
        search = '',
        category = 'all',
        sort = 'newest'
    } = params;

    const queryString = new URLSearchParams({
        page,
        limit,
        search,
        category,
        sort
    }).toString();

    return await apiCall(`/api/articles?${queryString}`);
}

/**
 * Get chi tiết 1 article
 * @param {string} articleId - Article ID từ URL
 */
async function getArticleDetail(articleId) {
    return await apiCall(`/api/article/${articleId}`);
}

/**
 * Load AI insights (trending, report)
 */
async function loadInsights() {
    return await apiCall('/api/insights');
}

/**
 * Load dashboard statistics
 */
async function loadStats() {
    return await apiCall('/api/stats');
}

/**
 * Start crawler
 * @param {Object} config - Crawler configuration
 */
async function startCrawler(config = {}) {
    const {
        mode = 'single',
        headless = true
    } = config;

    return await apiCall('/api/crawler/start', {
        method: 'POST',
        body: JSON.stringify({ mode, headless })
    });
}

/**
 * Stop crawler
 */
async function stopCrawler() {
    return await apiCall('/api/crawler/stop', {
        method: 'POST'
    });
}

/**
 * Check crawler status
 */
async function getCrawlerStatus() {
    return await apiCall('/api/crawler/status');
}

/**
 * Export articles to Excel
 */
async function exportToExcel() {
    try {
        const response = await apiCall('/api/export/excel');

        // Create download link
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;

        // Get filename from Content-Disposition header or use default
        const contentDisposition = response.headers.get('content-disposition');
        let filename = 'yahoo_news_export.xlsx';
        if (contentDisposition) {
            const matches = /filename="?([^"]+)"?/.exec(contentDisposition);
            if (matches && matches[1]) {
                filename = matches[1];
            }
        }

        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();

        return { success: true, filename };
    } catch (error) {
        console.error('Export error:', error);
        throw error;
    }
}

// =========================
// UI UPDATE FUNCTIONS
// =========================

/**
 * Update connection status indicator
 */
function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connectionStatus');
    if (statusEl) {
        if (connected) {
            statusEl.innerHTML = '🟢 Đã kết nối';
            statusEl.style.color = '#4ECCA3';
        } else {
            statusEl.innerHTML = '🔴 Mất kết nối';
            statusEl.style.color = '#ff6b6b';
        }
    }
}

/**
 * Update crawler status
 */
function updateCrawlerStatus(running) {
    const statusEl = document.getElementById('crawlerStatus');
    const startBtn = document.getElementById('startCrawlerBtn');
    const stopBtn = document.getElementById('stopCrawlerBtn');

    if (statusEl) {
        if (running) {
            statusEl.innerHTML = '⏳ Đang crawl...';
            statusEl.style.color = '#ffd93d';
        } else {
            statusEl.innerHTML = '⏸️ Đã dừng';
            statusEl.style.color = '#95a5a6';
        }
    }

    // Enable/disable buttons
    if (startBtn) startBtn.disabled = running;
    if (stopBtn) stopBtn.disabled = !running;
}

/**
 * Add crawler log to UI
 */
function addCrawlerLog(message, timestamp) {
    const logsContainer = document.getElementById('crawlerLogs');
    if (!logsContainer) return;

    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';

    const time = new Date(timestamp).toLocaleTimeString('vi-VN');
    logEntry.innerHTML = `<span class="log-time">[${time}]</span> ${message}`;

    logsContainer.appendChild(logEntry);

    // Auto scroll to bottom
    logsContainer.scrollTop = logsContainer.scrollHeight;

    // Limit to 100 logs
    while (logsContainer.children.length > 100) {
        logsContainer.removeChild(logsContainer.firstChild);
    }
}

/**
 * Refresh articles list
 */
async function refreshArticles() {
    try {
        const currentPage = parseInt(document.getElementById('currentPage')?.textContent || '1');
        const searchTerm = document.getElementById('searchInput')?.value || '';
        const category = document.getElementById('categoryFilter')?.value || 'all';
        const sortBy = document.getElementById('sortFilter')?.value || 'newest';

        const data = await loadArticles({
            page: currentPage,
            search: searchTerm,
            category: category,
            sort: sortBy
        });

        if (data.success) {
            displayArticles(data.data);
            updatePagination(data.pagination);
        }
    } catch (error) {
        console.error('Refresh articles error:', error);
    }
}

/**
 * Refresh stats panel
 */
async function refreshStats() {
    try {
        const data = await loadStats();

        if (data.success) {
            const stats = data.data;

            // Update stat cards
            document.getElementById('totalArticles').textContent = stats.total_articles || 0;
            document.getElementById('newToday').textContent = stats.new_today || 0;
            document.getElementById('withComments').textContent = stats.with_comments || 0;
            document.getElementById('pendingCount').textContent = stats.pending || 0;
            document.getElementById('totalComments').textContent = stats.total_comments || 0;
            document.getElementById('aiEnhanced').textContent = stats.ai_enhanced || 0;
            document.getElementById('aiCost').textContent = `$${(stats.ai_cost || 0).toFixed(4)}`;

            // Update last crawl time
            if (stats.crawled_at) {
                const crawlTime = new Date(stats.crawled_at).toLocaleString('vi-VN');
                document.getElementById('lastCrawl').textContent = crawlTime;
            }
        }
    } catch (error) {
        console.error('Refresh stats error:', error);
    }
}

/**
 * Display articles trong UI
 */
function displayArticles(articles) {
    const container = document.getElementById('articlesContainer');
    if (!container) return;

    // Clear existing articles
    container.innerHTML = '';

    if (!articles || articles.length === 0) {
        container.innerHTML = '<div class="no-data">Không có bài viết nào</div>';
        return;
    }

    // Create article cards
    articles.forEach(article => {
        const card = createArticleCard(article);
        container.appendChild(card);
    });
}

/**
 * Create article card element
 */
function createArticleCard(article) {
    const card = document.createElement('div');
    card.className = 'article-card';
    card.onclick = () => openArticleModal(article);

    // Extract data
    const title = article.title || 'Không có tiêu đề';
    const source = article.source || 'Unknown';
    const date = article.published_date || article.crawled_at || '';
    const commentCount = article.comments_data?.total_comments || 0;
    const qualityScore = article.ai_quality?.overall_score || 0;
    const summary = article.ai_summary?.summary || 'Chưa có tóm tắt AI';
    const categories = article.ai_categories?.tags || [];

    // Format date
    let formattedDate = '';
    if (date) {
        try {
            formattedDate = new Date(date).toLocaleString('vi-VN');
        } catch (e) {
            formattedDate = date;
        }
    }

    // Quality badge
    let qualityClass = 'quality-low';
    if (qualityScore >= 8) qualityClass = 'quality-high';
    else if (qualityScore >= 6) qualityClass = 'quality-medium';

    card.innerHTML = `
        <div class="article-header">
            <h3 class="article-title">${title}</h3>
            <span class="quality-badge ${qualityClass}">${qualityScore.toFixed(1)}</span>
        </div>
        <p class="article-summary">${summary}</p>
        <div class="article-meta">
            <span>📰 ${source}</span>
            <span>📅 ${formattedDate}</span>
            <span>💬 ${commentCount} bình luận</span>
        </div>
        ${categories.length > 0 ? `
            <div class="article-tags">
                ${categories.map(tag => `<span class="tag">${tag}</span>`).join('')}
            </div>
        ` : ''}
    `;

    return card;
}

/**
 * Update pagination info
 */
function updatePagination(pagination) {
    if (!pagination) return;

    document.getElementById('currentPage').textContent = pagination.page;
    document.getElementById('totalPages').textContent = pagination.total_pages;
    document.getElementById('showingCount').textContent = pagination.total;

    // Enable/disable prev/next buttons
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');

    if (prevBtn) prevBtn.disabled = pagination.page <= 1;
    if (nextBtn) nextBtn.disabled = pagination.page >= pagination.total_pages;
}

/**
 * Open article detail modal
 */
async function openArticleModal(article) {
    // Extract article ID from URL
    const urlParts = article.url.split('/');
    const articleId = urlParts[urlParts.length - 1];

    try {
        // Fetch full details
        const response = await getArticleDetail(articleId);

        if (response.success) {
            const fullArticle = response.data;
            showArticleModal(fullArticle);
        } else {
            // Fallback to existing data
            showArticleModal(article);
        }
    } catch (error) {
        console.error('Error loading article details:', error);
        // Fallback to existing data
        showArticleModal(article);
    }
}

/**
 * Show article modal với data
 */
function showArticleModal(article) {
    const modal = document.getElementById('articleModal');
    if (!modal) return;

    // Populate modal content
    document.getElementById('modalTitle').textContent = article.title || 'Không có tiêu đề';
    document.getElementById('modalSource').textContent = article.source || 'Unknown';
    document.getElementById('modalDate').textContent = article.published_date || article.crawled_at || '';
    document.getElementById('modalComments').textContent = article.comments_data?.total_comments || 0;
    document.getElementById('modalQuality').textContent = (article.ai_quality?.overall_score || 0).toFixed(1);

    // AI Summary
    const summary = article.ai_summary?.summary || 'Chưa có tóm tắt AI';
    const keyPoints = article.ai_summary?.key_points || [];

    document.getElementById('modalSummary').textContent = summary;

    const keyPointsList = document.getElementById('modalKeyPoints');
    keyPointsList.innerHTML = '';
    keyPoints.forEach(point => {
        const li = document.createElement('li');
        li.textContent = point;
        keyPointsList.appendChild(li);
    });

    // Categories
    const categories = article.ai_categories?.tags || [];
    const categoriesContainer = document.getElementById('modalCategories');
    categoriesContainer.innerHTML = categories.map(tag =>
        `<span class="tag">${tag}</span>`
    ).join('') || '<span>Chưa phân loại</span>';

    // Sentiment
    const sentiment = article.ai_sentiment?.overall_sentiment || {};
    document.getElementById('sentimentPositive').textContent =
        `${((sentiment.positive || 0) * 100).toFixed(1)}%`;
    document.getElementById('sentimentNeutral').textContent =
        `${((sentiment.neutral || 0) * 100).toFixed(1)}%`;
    document.getElementById('sentimentNegative').textContent =
        `${((sentiment.negative || 0) * 100).toFixed(1)}%`;

    // Update progress bars
    document.querySelector('#sentimentPositive').parentElement.querySelector('.sentiment-bar').style.width =
        `${(sentiment.positive || 0) * 100}%`;
    document.querySelector('#sentimentNeutral').parentElement.querySelector('.sentiment-bar').style.width =
        `${(sentiment.neutral || 0) * 100}%`;
    document.querySelector('#sentimentNegative').parentElement.querySelector('.sentiment-bar').style.width =
        `${(sentiment.negative || 0) * 100}%`;

    // Top comments
    const comments = article.comments_data?.comments || [];
    const topComments = comments.slice(0, 5);

    const commentsContainer = document.getElementById('modalCommentsList');
    commentsContainer.innerHTML = '';

    if (topComments.length > 0) {
        topComments.forEach(comment => {
            const div = document.createElement('div');
            div.className = 'comment-item';
            div.innerHTML = `
                <p>${comment.text || ''}</p>
                <small>👍 ${comment.likes || 0} likes</small>
            `;
            commentsContainer.appendChild(div);
        });
    } else {
        commentsContainer.innerHTML = '<p>Chưa có bình luận</p>';
    }

    // Show modal
    modal.style.display = 'block';
}

/**
 * Close article modal
 */
function closeModal() {
    const modal = document.getElementById('articleModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// =========================
// INITIALIZATION
// =========================

/**
 * Initialize API client khi page load
 */
function initAPI() {
    console.log('Initializing API client...');

    // Initialize WebSocket
    initWebSocket();

    // Load initial data
    refreshArticles();
    refreshStats();
    getCrawlerStatus().then(response => {
        if (response.success) {
            updateCrawlerStatus(response.running);
        }
    });

    // Auto-refresh every 30 seconds
    setInterval(() => {
        refreshStats();
    }, 30000);

    console.log('✓ API client initialized');
}

// Export functions for global use
window.API = {
    init: initAPI,
    loadArticles,
    getArticleDetail,
    loadInsights,
    loadStats,
    startCrawler,
    stopCrawler,
    getCrawlerStatus,
    exportToExcel,
    refreshArticles,
    refreshStats,
    closeModal
};

"""
YAHOO NEWS AI CRAWLER - FLASK BACKEND API
==========================================

REST API server để kết nối Dashboard với Crawler.

Features:
- Load articles từ JSON files
- Real-time crawl status
- WebSocket updates
- Export to Excel/PDF
- Start/Stop crawler

Author: Claude Code + User
"""

import sys
import os

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    try:
        import codecs
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import json
import os
import glob
from datetime import datetime
import pandas as pd
from io import BytesIO
import subprocess
import threading

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
socketio = SocketIO(app, cors_allowed_origins="*")

# Global crawler process
crawler_process = None
crawler_running = False

# =========================
# HELPER FUNCTIONS
# =========================

def get_latest_json_file(pattern="yahoo_news_ai_*.json"):
    """Lấy file JSON mới nhất"""
    files = glob.glob(pattern)
    if not files:
        return None
    # Sort by modification time
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def load_json_data(filename):
    """Load data từ JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}

def get_all_articles():
    """Lấy tất cả articles từ file mới nhất"""
    latest_file = get_latest_json_file()
    if not latest_file:
        return {"articles": [], "metadata": {}}

    data = load_json_data(latest_file)
    return data

def get_trending_insights():
    """Lấy trending insights từ file AI"""
    latest_file = get_latest_json_file("ai_insights_*.json")
    if not latest_file:
        return None

    return load_json_data(latest_file)

# =========================
# API ENDPOINTS
# =========================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "service": "Yahoo News AI Crawler API",
        "version": "3.0",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/articles', methods=['GET'])
def get_articles():
    """
    GET /api/articles

    Query params:
    - limit: Số lượng bài (default: 10)
    - page: Trang số (default: 1)
    - search: Tìm kiếm theo keyword
    - category: Filter theo category
    - sort: Sắp xếp (newest, quality, comments)
    """
    # Get query params
    limit = int(request.args.get('limit', 10))
    page = int(request.args.get('page', 1))
    search = request.args.get('search', '').lower()
    category = request.args.get('category', 'all')
    sort_by = request.args.get('sort', 'newest')

    # Load data
    data = get_all_articles()
    articles = data.get('articles', [])

    # Filter by search
    if search:
        articles = [
            a for a in articles
            if search in a.get('title', '').lower() or
               search in str(a.get('ai_summary', {}).get('summary', '')).lower()
        ]

    # Filter by category
    if category != 'all':
        articles = [
            a for a in articles
            if category.lower() in str(a.get('ai_categories', {}).get('tags', [])).lower()
        ]

    # Sort
    if sort_by == 'quality':
        articles.sort(
            key=lambda x: x.get('ai_quality', {}).get('overall_score', 0),
            reverse=True
        )
    elif sort_by == 'comments':
        articles.sort(
            key=lambda x: x.get('comments_data', {}).get('total_comments', 0),
            reverse=True
        )
    # Default: newest (already in order)

    # Pagination
    start = (page - 1) * limit
    end = start + limit
    paginated = articles[start:end]

    return jsonify({
        "success": True,
        "data": paginated,
        "metadata": data.get('metadata', {}),
        "pagination": {
            "page": page,
            "limit": limit,
            "total": len(articles),
            "total_pages": (len(articles) + limit - 1) // limit
        }
    })

@app.route('/api/article/<article_id>', methods=['GET'])
def get_article_detail(article_id):
    """GET /api/article/<id> - Lấy chi tiết 1 bài"""
    data = get_all_articles()
    articles = data.get('articles', [])

    # Find article by ID (extract from URL)
    for article in articles:
        if article_id in article.get('url', ''):
            return jsonify({
                "success": True,
                "data": article
            })

    return jsonify({
        "success": False,
        "error": "Article not found"
    }), 404

@app.route('/api/insights', methods=['GET'])
def get_insights():
    """GET /api/insights - Lấy AI insights (trending, report)"""
    insights = get_trending_insights()

    if not insights:
        return jsonify({
            "success": False,
            "error": "No insights available"
        }), 404

    return jsonify({
        "success": True,
        "data": insights
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """GET /api/stats - Lấy thống kê tổng quan"""
    data = get_all_articles()
    articles = data.get('articles', [])
    metadata = data.get('metadata', {})

    # Calculate stats
    total_articles = len(articles)
    with_comments = len([a for a in articles if a.get('comments_data', {}).get('total_comments', 0) > 0])
    total_comments = sum([a.get('comments_data', {}).get('total_comments', 0) for a in articles])
    ai_enhanced = len([a for a in articles if 'ai_summary' in a])

    # Check pending comments
    pending_count = 0
    if os.path.exists('pending_comments.json'):
        with open('pending_comments.json', 'r', encoding='utf-8') as f:
            pending_data = json.load(f)
            pending_count = len(pending_data.get('articles_pending', []))

    return jsonify({
        "success": True,
        "data": {
            "total_articles": total_articles,
            "new_today": metadata.get('total_articles', 0),
            "with_comments": with_comments,
            "pending": pending_count,
            "total_comments": total_comments,
            "ai_enhanced": ai_enhanced,
            "ai_cost": metadata.get('ai_cost', 0),
            "crawled_at": metadata.get('crawled_at'),
            "search_keyword": metadata.get('search_keyword')
        }
    })

@app.route('/api/crawler/start', methods=['POST'])
def start_crawler():
    """POST /api/crawler/start - Bắt đầu crawl"""
    global crawler_process, crawler_running

    if crawler_running:
        return jsonify({
            "success": False,
            "error": "Crawler is already running"
        }), 400

    # Get config from request
    config = request.json or {}
    mode = config.get('mode', 'single')
    headless = config.get('headless', True)

    # Build command
    cmd = ['python', 'crawl_yahoo_news_ai.py']
    if mode == 'single':
        cmd.append('--single')
    if headless:
        cmd.append('--headless')

    # Start crawler in background
    try:
        crawler_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        crawler_running = True

        # Start thread to monitor output
        def monitor_crawler():
            global crawler_running
            for line in crawler_process.stdout:
                # Send updates via WebSocket
                socketio.emit('crawler_log', {
                    'message': line.strip(),
                    'timestamp': datetime.now().isoformat()
                })
            crawler_running = False
            socketio.emit('crawler_status', {'running': False})

        threading.Thread(target=monitor_crawler, daemon=True).start()

        return jsonify({
            "success": True,
            "message": "Crawler started",
            "pid": crawler_process.pid
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/crawler/stop', methods=['POST'])
def stop_crawler():
    """POST /api/crawler/stop - Dừng crawl"""
    global crawler_process, crawler_running

    if not crawler_running or not crawler_process:
        return jsonify({
            "success": False,
            "error": "No crawler is running"
        }), 400

    try:
        crawler_process.terminate()
        crawler_process.wait(timeout=5)
        crawler_running = False

        return jsonify({
            "success": True,
            "message": "Crawler stopped"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/crawler/status', methods=['GET'])
def crawler_status():
    """GET /api/crawler/status - Kiểm tra trạng thái crawler"""
    return jsonify({
        "success": True,
        "running": crawler_running,
        "pid": crawler_process.pid if crawler_process else None
    })

@app.route('/api/export/excel', methods=['GET'])
def export_excel():
    """GET /api/export/excel - Export articles to Excel"""
    data = get_all_articles()
    articles = data.get('articles', [])

    if not articles:
        return jsonify({"error": "No articles to export"}), 404

    # Prepare data for Excel
    rows = []
    for article in articles:
        rows.append({
            'URL': article.get('url'),
            'Title': article.get('title'),
            'Date': article.get('published_date'),
            'Source': article.get('source'),
            'Comments': article.get('comments_data', {}).get('total_comments', 0),
            'AI Summary': article.get('ai_summary', {}).get('summary', ''),
            'Quality Score': article.get('ai_quality', {}).get('overall_score'),
            'Categories': ', '.join(article.get('ai_categories', {}).get('tags', [])),
            'Crawled At': article.get('crawled_at')
        })

    # Create Excel file
    df = pd.DataFrame(rows)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Articles')

    output.seek(0)

    filename = f"yahoo_news_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

# =========================
# WEBSOCKET EVENTS
# =========================

@socketio.on('connect')
def handle_connect():
    """Client connected"""
    print('Client connected')
    emit('connection', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected"""
    print('Client disconnected')

@socketio.on('request_update')
def handle_update_request():
    """Client requests data update"""
    data = get_all_articles()
    emit('articles_update', data)

# =========================
# MAIN
# =========================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 YAHOO NEWS AI CRAWLER - API SERVER")
    print("="*60)
    print("📡 Server: http://localhost:5000")
    print("📊 API Docs: http://localhost:5000/api/health")
    print("🔌 WebSocket: ws://localhost:5000")
    print("="*60 + "\n")

    # Run server
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

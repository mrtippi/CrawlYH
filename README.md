# 🤖 YAHOO NEWS AI CRAWLER

![Version](https://img.shields.io/badge/version-3.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)

**Hệ thống crawl tin tức Yahoo News tự động với AI phân tích và Dashboard web quản lý**

---

## 📋 MỤC LỤC

- [Tổng Quan](#-tổng-quan)
- [Tính Năng Chính](#-tính-năng-chính)  
- [Kiến Trúc Hệ Thống](#-kiến-trúc-hệ-thống)
- [Yêu Cầu Hệ Thống](#-yêu-cầu-hệ-thống)
- [Cài Đặt](#-cài-đặt)
- [Cấu Hình](#-cấu-hình)
- [Sử Dụng](#-sử-dụng)
- [Cấu Trúc Dữ Liệu](#-cấu-trúc-dữ-liệu)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 TỔNG QUAN

Yahoo News AI Crawler là một hệ thống full-stack hoàn chỉnh để:
- **Crawl tự động** tin tức từ Yahoo News Japan với từ khóa tùy chỉnh
- **Phân tích AI** bằng Claude 3.5 Sonnet cho 8 use cases
- **Dashboard web** để quản lý, giám sát và xuất dữ liệu  
- **Crawl 2 phase** thông minh: crawl bài viết → chờ 30 phút → re-crawl comments
- **Lọc trùng lặp** thông minh với cơ chế "Crawl Until Known ID"

---

## 🚀 TÍNH NĂNG CHÍNH

### 1. 🕷️ Web Crawling

- **SeleniumBase UC Mode**: Bypass detection, crawl ổn định
- **Pagination tự động**: Crawl toàn bộ comments qua nhiều trang
- **Ad filtering**: Lọc quảng cáo (広告) tự động
- **Duplicate detection**: Tránh crawl trùng với cơ chế "Crawl Until Known ID"
- **Headless mode**: Chạy ẩn browser để tiết kiệm tài nguyên

### 2. 🤖 AI Analysis (Claude 3.5 Sonnet)

8 tính năng AI:
- 📝 **Tóm Tắt** - Summary + key points
- 😊 **Phân Tích Cảm Xúc** - Sentiment analysis
- 🔥 **Phát Hiện Xu Hướng** - Trending topics
- 🏷️ **Phân Loại** - Auto categorization + tags
- ❓ **Q&A** - Answer questions about article
- 🚨 **Phát Hiện Bất Thường** - Detect fake news, clickbait
- ⭐ **Đánh Giá Chất Lượng** - Quality score 1-10
- 📊 **Báo Cáo Hàng Ngày** - Daily insights report

**💰 Chi phí:** ~$0.009 USD/bài viết

### 3. 🌐 Web Dashboard

- **Control Panel**: Start/stop crawler, cấu hình
- **Articles View**: Search/filter/pagination
- **Real-time Stats**: Tổng bài, comments, chi phí AI
- **Article Details Modal**: Xem chi tiết + AI analysis
- **Export Excel**: Download toàn bộ dữ liệu

**Stack:** HTML5 + CSS3 + Vanilla JS + Flask + WebSocket

### 4. 🔄 2-Phase Crawling

**Phase 1:** Crawl bài viết mới
- Lấy title, content, metadata
- Nếu có comments → crawl ngay
- Nếu không → add vào pending list

**⏰ Chờ 30 phút**

**Phase 2:** Re-crawl comments  
- Crawl ONLY comments (không crawl lại content)
- Update JSON + AI Sentiment
- Remove khỏi pending list

**Files:** `last_crawl.json`, `pending_comments.json`

---

## 💻 YÊU CẦU HỆ THỐNG

- **RAM**: 4GB+ (khuyến nghị 8GB+)
- **Python**: 3.10+
- **OS**: Windows 10/11, macOS, Linux
- **Network**: Internet ổn định
- **API Key**: Claude API từ Anthropic Console

---

## 📦 CÀI ĐẶT

**Bước 1:** Clone/Download project

**Bước 2:** Cài dependencies
```bash
pip install -r requirements.txt
```

**Bước 3:** Cài Chrome Driver (tự động)
```bash
sbase install chromedriver
```

---

## ⚙️ CẤU HÌNH

### 1. Claude API Key

Mở `claude_ai_analyzer.py` và thay API key:

```python
def __init__(self, api_key: str = "YOUR_API_KEY"):
    self.client = anthropic.Anthropic(api_key=api_key)
```

### 2. Từ Khóa Tìm Kiếm  

Mở `crawl_yahoo_news_ai.py`, dòng 585:

```python
search_keyword = "大谷翔平"  # Thay từ khóa của bạn
```

**Từ khóa phổ biến:**
- `大谷翔平` - Shohei Ohtani
- `ダルビッシュ有` - Yu Darvish  
- `サッカー` - Soccer
- `野球` - Baseball

---

## 🎮 SỬ DỤNG

### 🖥️ Option 1: Web Dashboard (Khuyến Nghị)

**Bước 1:** Start Flask Backend
```bash
python app.py
```

**Bước 2:** Mở Dashboard
```bash
start index.html  # Windows
open index.html   # macOS
```

**Bước 3:** Sử dụng
1. Chờ kết nối (🟢 Đã kết nối)
2. Cấu hình ở Control Panel
3. Click "🚀 Bắt Đầu Crawl"
4. Theo dõi real-time
5. Click bài viết để xem chi tiết
6. Export Excel khi cần

### ⌨️ Option 2: Command Line

**Crawl 1 lần:**
```bash
python crawl_yahoo_news_ai.py --single
```

**Crawl headless:**
```bash
python crawl_yahoo_news_ai.py --single --headless
```

**Crawl liên tục (30 phút/lần):**
```bash
python crawl_yahoo_news_ai.py --continuous
```

**Re-crawl comments only:**
```bash
python crawl_yahoo_news_ai.py --recrawl-comments
```

---

## 📊 CẤU TRÚC DỮ LIỆU

### Output Files

- `yahoo_news_ai_YYYYMMDD_HHMMSS.json` - Dữ liệu crawl
- `ai_insights_YYYYMMDD_HHMMSS.json` - AI analysis
- `last_crawl.json` - Tracking (lọc trùng)
- `pending_comments.json` - Pending re-crawl list

### Article Schema

```json
{
  "url": "https://news.yahoo.co.jp/articles/...",
  "title": "大谷翔平、MVP獲得",
  "source": "Yahoo News Japan",
  "published_date": "10/21(火) 16:58",
  "comments_data": {
    "total_comments": 156,
    "comments": [...]
  },
  "ai_summary": {
    "summary": "Ohtani giành MVP...",
    "key_points": ["..."]
  },
  "ai_sentiment": {
    "overall_sentiment": {
      "positive": 0.85,
      "neutral": 0.12,
      "negative": 0.03
    }
  },
  "ai_quality": {
    "overall_score": 8.5
  }
}
```

---

## 🔧 TROUBLESHOOTING

### 1. Chrome Driver Issues

**Lỗi:** `ChromeDriver not found`

**Fix:**
```bash
sbase install chromedriver
```

### 2. Comments Không Crawl Được

**Nguyên nhân:** Yahoo News thay đổi HTML structure

**Giải pháp:**
- Sử dụng 2-phase crawling
- Bài viết tự động re-crawl sau 30 phút

### 3. AI API Rate Limit

**Lỗi:** `429 Too Many Requests`

**Fix:**
- Giảm `ai_batch_size` xuống 5
- Thêm delay giữa các batch

### 4. Flask Server Không Start

**Lỗi:** `Address already in use`

**Fix:**
```bash
taskkill /F /IM python.exe  # Windows
lsof -ti:5000 | xargs kill  # macOS/Linux
```

---

## 📂 CẤU TRÚC THỦ MỤC

```
d:\CrawlYH\
│
├── 📄 crawl_yahoo_news_ai.py      # Main crawler (V3.0)
├── 📄 claude_ai_analyzer.py       # AI module
├── 📄 app.py                       # Flask backend
│
├── 🌐 index.html                   # Dashboard
├── 📜 api.js                       # API client
│
├── 📋 requirements.txt             # Dependencies
├── 📖 README.md                    # Documentation
├── 🚫 .gitignore                   # Git ignore
│
├── 📊 Data Files (auto-generated):
│   ├── yahoo_news_ai_*.json       # Articles
│   ├── ai_insights_*.json         # AI analysis
│   ├── last_crawl.json            # Tracking
│   └── pending_comments.json      # Pending list
│
└── 📁 backup_old_files_20251021/  # Backup code cũ
```

---

## 🏗️ KIẾN TRÚC HỆ THỐNG

```
┌──────────────────────────────────────────┐
│     WEB DASHBOARD (index.html)           │
│  Control Panel | Articles | Stats        │
└──────────────────────────────────────────┘
              ↕ WebSocket + REST API
┌──────────────────────────────────────────┐
│       FLASK BACKEND (app.py)             │
│  10 REST Endpoints | WebSocket Server    │
└──────────────────────────────────────────┘
              ↕ JSON Files
┌──────────────────────────────────────────┐
│    CRAWLER (crawl_yahoo_news_ai.py)      │
│  SeleniumBase | 2-Phase | Ad Filter      │
└──────────────────────────────────────────┘
              ↕ API Calls
┌──────────────────────────────────────────┐
│      AI MODULE (claude_ai_analyzer.py)   │
│  8 AI Use Cases | Cost Tracking          │
└──────────────────────────────────────────┘
              ↕
        ☁️ Anthropic Claude API
```

---

## 📡 API ENDPOINTS

| Method | Endpoint | Mô Tả |
|--------|----------|-------|
| GET | `/api/health` | Health check |
| GET | `/api/articles` | List articles (pagination, search, filter) |
| GET | `/api/article/<id>` | Chi tiết 1 bài |
| GET | `/api/insights` | AI insights |
| GET | `/api/stats` | Dashboard stats |
| POST | `/api/crawler/start` | Start crawler |
| POST | `/api/crawler/stop` | Stop crawler |
| GET | `/api/crawler/status` | Check status |
| GET | `/api/export/excel` | Export Excel |

---

## 📝 LICENSE

MIT License

---

## 👨‍💻 AUTHOR

Created by Claude Code + User
Last Updated: 2025-10-21
Version: 3.0

---

**⭐ Nếu project hữu ích, hãy cho star!**

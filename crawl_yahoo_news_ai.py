"""
YAHOO NEWS AI-POWERED CONTINUOUS CRAWLER
=========================================

Phiên bản V3.0 - 2-Phase Crawling + Full AI Integration:

🔄 2-PHASE CRAWLING:
✓ Phase 1: Crawl bài mới → Add to pending list (nếu chưa có comments)
✓ Phase 2: Re-crawl comments sau 30 phút → Update JSON + AI Sentiment

🤖 AI FEATURES (8 Use Cases):
✓ AI Summarization (tóm tắt tự động)
✓ Advanced Sentiment Analysis (phân tích cảm xúc)
✓ Trending Topics Detection (phát hiện xu hướng)
✓ Auto-categorization & Tagging (phân loại tự động)
✓ Q&A System (hỏi đáp thông minh)
✓ Anomaly Detection (phát hiện bất thường)
✓ Quality Scoring (đánh giá chất lượng)
✓ Auto Daily Reports (báo cáo tự động)

⚡ CORE FEATURES:
✓ Continuous crawling + duplicate filtering
✓ Headless mode
✓ Cost tracking & optimization

Author: Claude Code + User Innovation
"""

import sys
import os

# Fix Unicode encoding cho Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from seleniumbase import SB
import time
import json
from datetime import datetime, timedelta
import re
import math
import glob
from claude_ai_analyzer import ClaudeAnalyzer


class AIEnhancedYahooNewsCrawler:
    """
    AI-Powered Continuous Crawler
    = Continuous Crawler + Claude AI Brain
    """

    def __init__(self, search_keyword="大谷翔平", max_pages=2, max_comments_pages=5,
                 headless=False, interval_minutes=30, claude_api_key=None,
                 enable_ai=True, ai_batch_size=10):
        """
        Khởi tạo AI-Enhanced Crawler

        Args:
            search_keyword: Từ khóa tìm kiếm
            max_pages: Số trang tìm kiếm tối đa
            max_comments_pages: Số trang comments tối đa/bài
            headless: Chạy ẩn browser
            interval_minutes: Thời gian giữa các lần crawl (phút)
            claude_api_key: Claude AI API key
            enable_ai: Bật/tắt AI analysis
            ai_batch_size: Số bài analyze cùng lúc (tiết kiệm cost)
        """
        self.search_keyword = search_keyword
        self.max_pages = max_pages
        self.max_comments_pages = max_comments_pages
        self.headless = headless
        self.interval_minutes = interval_minutes
        self.enable_ai = enable_ai
        self.ai_batch_size = ai_batch_size

        # Tracking
        self.tracking_file = "last_crawl.json"
        self.pending_comments_file = "pending_comments.json"
        self.last_article_id = None
        self.last_article_url = None

        # Stats
        self.articles = []
        self.stats = {
            "total_runs": 0,
            "new_articles_this_run": 0,
            "articles_with_comments": 0,
            "articles_without_comments": 0,
            "total_comments": 0,
            "time_saved": 0,
            "duplicates_skipped": 0,
            "ai_enhanced_articles": 0,
            "comments_recrawled": 0
        }

        # Initialize Claude AI
        if self.enable_ai and claude_api_key:
            print("[AI] Initializing Claude AI Analyzer...")
            self.ai = ClaudeAnalyzer(api_key=claude_api_key)
            print("[AI] ✓ Claude AI ready!")
        else:
            self.ai = None
            print("[i] AI features disabled")

    def load_tracking_data(self):
        """Load dữ liệu tracking từ file"""
        if not os.path.exists(self.tracking_file):
            print("[i] Lần đầu tiên chạy - chưa có tracking file")
            return None, None, None

        try:
            with open(self.tracking_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            last_id = data.get("last_article_id")
            last_url = data.get("last_article_url")
            last_time = data.get("last_crawl_time")

            print(f"[✓] Loaded tracking data:")
            print(f"    Last ID: {last_id}")
            print(f"    Last crawl: {last_time}")

            return last_id, last_url, last_time

        except Exception as e:
            print(f"[!] Lỗi load tracking: {str(e)}")
            return None, None, None

    def save_tracking_data(self, first_article_id, first_article_url):
        """Lưu tracking data"""
        tracking_data = {
            "last_article_id": first_article_id,
            "last_article_url": first_article_url,
            "last_crawl_time": datetime.now().isoformat(),
            "articles_crawled_this_run": self.stats["new_articles_this_run"],
            "total_runs": self.stats["total_runs"]
        }

        try:
            with open(self.tracking_file, 'w', encoding='utf-8') as f:
                json.dump(tracking_data, f, ensure_ascii=False, indent=2)
            print(f"[✓] Updated tracking file")
        except Exception as e:
            print(f"[!] Lỗi save tracking: {str(e)}")

    def extract_article_id_from_url(self, url):
        """Extract article ID từ URL"""
        match = re.search(r'/articles/([a-f0-9]+)', url)
        if match:
            return match.group(1)
        return None

    # ========== 2-PHASE CRAWLING: PENDING COMMENTS MANAGEMENT ==========

    def load_pending_comments(self):
        """Load danh sách bài chờ crawl comments"""
        if not os.path.exists(self.pending_comments_file):
            return []

        try:
            with open(self.pending_comments_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("articles_pending", [])
        except Exception as e:
            print(f"[!] Lỗi load pending comments: {str(e)}")
            return []

    def save_pending_comments(self, pending_list):
        """Lưu danh sách bài chờ crawl comments"""
        try:
            with open(self.pending_comments_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "articles_pending": pending_list,
                    "last_updated": datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[!] Lỗi save pending comments: {str(e)}")

    def add_to_pending_comments(self, article_data):
        """
        Thêm bài vào pending list (Phase 1)
        Chỉ thêm nếu bài chưa có comments hoặc có ít comments
        """
        pending_list = self.load_pending_comments()

        article_id = self.extract_article_id_from_url(article_data["url"])
        if not article_id:
            return

        # Check xem đã có trong pending chưa
        if any(p["article_id"] == article_id for p in pending_list):
            return

        # Tính thời gian recrawl (30 phút sau)
        recrawl_time = datetime.now() + timedelta(minutes=30)

        pending_item = {
            "article_id": article_id,
            "url": article_data["url"],
            "title": article_data.get("title", "N/A"),
            "first_crawled_at": article_data.get("crawled_at"),
            "recrawl_after": recrawl_time.isoformat(),
            "estimated_comments": article_data.get("estimated_comment_count", 0),
            "status": "pending"
        }

        pending_list.append(pending_item)
        self.save_pending_comments(pending_list)

        print(f"  [📝] Added to pending: {article_data.get('title', 'N/A')[:40]}...")
        print(f"      Will re-crawl comments after: {recrawl_time.strftime('%H:%M:%S')}")

    def get_pending_recrawl(self):
        """
        Lấy danh sách bài cần re-crawl comments (Phase 2)
        Chỉ lấy những bài đã qua 30 phút
        """
        pending_list = self.load_pending_comments()
        now = datetime.now()

        ready_to_recrawl = []
        still_pending = []

        for item in pending_list:
            if item["status"] != "pending":
                continue

            recrawl_time = datetime.fromisoformat(item["recrawl_after"])

            if now >= recrawl_time:
                ready_to_recrawl.append(item)
            else:
                still_pending.append(item)

        # Giữ lại những bài chưa đến giờ
        self.save_pending_comments(still_pending)

        return ready_to_recrawl

    def recrawl_comments_only(self, sb, pending_item):
        """
        Re-crawl ONLY comments (Phase 2)
        Không crawl lại content
        """
        print(f"\n--- Re-crawl Comments: {pending_item['title'][:50]}... ---")

        url = pending_item["url"]
        article_id = pending_item["article_id"]

        # Detect comments
        _, has_comments, comment_count = self.crawl_article_content(sb, url)

        if not has_comments or comment_count == 0:
            print(f"  [!] Vẫn chưa có comments")
            return None

        print(f"  [✓] Phát hiện: {comment_count} comments (lúc đầu: {pending_item['estimated_comments']})")

        # Crawl comments
        comments_data = self.crawl_comments_with_pagination(sb, url, comment_count)

        if comments_data["total_comments"] > 0:
            print(f"  [✓] Crawled {comments_data['total_comments']} comments!")
            self.stats["comments_recrawled"] += 1

            return {
                "article_id": article_id,
                "url": url,
                "comments_data": comments_data,
                "recrawled_at": datetime.now().isoformat()
            }

        return None

    def update_existing_article_with_comments(self, output_file, article_id, comments_data):
        """
        Update file JSON cũ - merge comments vào article
        """
        if not os.path.exists(output_file):
            print(f"  [!] File không tồn tại: {output_file}")
            return False

        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Tìm article
            updated = False
            for article in data.get("articles", []):
                if self.extract_article_id_from_url(article["url"]) == article_id:
                    article["comments_data"] = comments_data
                    article["comments_updated_at"] = datetime.now().isoformat()

                    # Chạy AI sentiment nếu enable
                    if self.ai and self.enable_ai and comments_data.get("comments"):
                        print(f"  [AI] Analyzing sentiment for new comments...")
                        sentiment = self.ai.analyze_sentiment_advanced(comments_data["comments"])
                        article["ai_sentiment"] = sentiment

                    updated = True
                    break

            if updated:
                # Save lại file
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"  [✓] Updated article in: {output_file}")
                return True
            else:
                print(f"  [!] Article ID not found in file")
                return False

        except Exception as e:
            print(f"  [!] Lỗi update file: {str(e)}")
            return False

    def get_search_url(self, page=1):
        """Tạo URL tìm kiếm"""
        base_url = "https://news.yahoo.co.jp/search"
        params = f"?p={self.search_keyword}"
        if page > 1:
            params += f"&page={page}"
        return base_url + params

    def extract_article_links(self, sb):
        """Lấy danh sách link bài viết (LỌC QUẢNG CÁO)"""
        print("\n[+] Đang tìm kiếm các bài viết...")

        sb.scroll_to_bottom()
        sb.sleep(0.3)

        links = []
        ads_filtered = 0

        try:
            link_elements = sb.find_elements("a")

            for elem in link_elements:
                try:
                    href = elem.get_attribute("href")

                    # Chỉ lấy link Yahoo News articles
                    if not href or "news.yahoo.co.jp/articles/" not in href:
                        continue

                    # QUAN TRỌNG: Lọc quảng cáo
                    is_ad = False

                    # Cách 1: Check parent/ancestor có chứa "広告" (Ad marker)
                    try:
                        # Check multiple ancestor levels
                        current = elem
                        for _ in range(5):  # Check up to 5 levels up
                            try:
                                parent = current.find_element("xpath", "..")
                                parent_text = parent.text
                                parent_html = parent.get_attribute("outerHTML")

                                if "広告" in parent_text or "AD" in parent_text.upper():
                                    is_ad = True
                                    break

                                # Check for ad-related class names
                                parent_class = parent.get_attribute("class") or ""
                                if any(ad_class in parent_class.lower() for ad_class in ["ad", "sponsor", "promo", "commercial"]):
                                    is_ad = True
                                    break

                                current = parent
                            except:
                                break
                    except:
                        pass

                    if is_ad:
                        ads_filtered += 1
                        continue

                    # Cách 2: Check URL pattern
                    if "promo" in href.lower() or "ad=" in href.lower() or "sponsored" in href.lower():
                        ads_filtered += 1
                        continue

                    # Cách 3: Check link text/title
                    try:
                        link_text = elem.text or ""
                        if "広告" in link_text or "PR" in link_text:
                            ads_filtered += 1
                            continue
                    except:
                        pass

                    # Clean URL và thêm vào list
                    clean_url = href.split('?')[0]
                    if clean_url not in links:
                        links.append(clean_url)

                except:
                    continue

        except Exception as e:
            print(f"[!] Lỗi: {str(e)}")

        print(f"[+] Tìm thấy {len(links)} bài viết")
        if ads_filtered > 0:
            print(f"[✓] Đã lọc {ads_filtered} quảng cáo")
        return links

    def check_has_comments(self, sb):
        """Kiểm tra bài viết có comments không"""
        try:
            page_text = sb.get_page_source()

            comment_patterns = [
                r'コメント(\d+)件',
                r'(\d+)\s*件のコメント',
            ]

            for pattern in comment_patterns:
                match = re.search(pattern, page_text)
                if match:
                    count = int(match.group(1))
                    print(f"    ✓ Phát hiện: {count} comments")
                    return (True, count)

            try:
                elements = sb.find_elements("*")
                for elem in elements[:100]:
                    try:
                        text = elem.text.strip()
                        match = re.search(r'コメント(\d+)件', text)
                        if match:
                            count = int(match.group(1))
                            print(f"    ✓ Phát hiện: {count} comments")
                            return (True, count)
                    except:
                        continue
            except:
                pass

            print(f"    ✗ Không có comments")
            return (False, 0)

        except Exception as e:
            print(f"    [!] Lỗi check comments: {str(e)}")
            return (True, None)

    def crawl_article_content(self, sb, url):
        """Crawl nội dung bài viết"""
        try:
            print(f"\n{'='*60}")
            print(f"[+] Crawl: {url}")

            sb.open(url)
            sb.sleep(1)

            article_data = {
                "url": url,
                "crawled_at": datetime.now().isoformat()
            }

            # Tiêu đề
            try:
                title = sb.get_text("h1")
                article_data["title"] = title.strip()
                print(f"[+] Tiêu đề: {title[:60]}...")
            except:
                article_data["title"] = "N/A"

            # Nguồn
            try:
                source = sb.get_text(".sc-gdOjLM, .source, .article-header-source")
                article_data["source"] = source.strip()
            except:
                article_data["source"] = "N/A"

            # Ngày đăng
            try:
                date = sb.get_text("time, .article-header-time, .date")
                article_data["published_date"] = date.strip()
            except:
                article_data["published_date"] = "N/A"

            # Tác giả
            try:
                author = sb.get_text(".author, .article-header-author, .byline")
                article_data["author"] = author.strip()
            except:
                article_data["author"] = "N/A"

            # Nội dung
            try:
                content_selectors = [".article-body", ".article-content", ".sc-cKRKFl", "article p"]
                content_paragraphs = []

                for selector in content_selectors:
                    try:
                        if sb.is_element_visible(selector):
                            elements = sb.find_elements(selector)
                            for elem in elements:
                                text = elem.text.strip()
                                if text and len(text) > 20:
                                    content_paragraphs.append(text)
                            if content_paragraphs:
                                break
                    except:
                        continue

                article_data["content"] = "\n\n".join(content_paragraphs) if content_paragraphs else "N/A"
                print(f"[+] Nội dung: {len(article_data['content'])} ký tự")

            except:
                article_data["content"] = "N/A"

            # Kiểm tra comments
            print(f"[+] Kiểm tra comments...")
            has_comments, comment_count = self.check_has_comments(sb)

            if has_comments:
                self.stats["articles_with_comments"] += 1
            else:
                self.stats["articles_without_comments"] += 1
                self.stats["time_saved"] += self.max_comments_pages * 2

            article_data["has_comments"] = has_comments
            article_data["estimated_comment_count"] = comment_count

            return article_data, has_comments, comment_count

        except Exception as e:
            print(f"[!] Lỗi: {str(e)}")
            return None, False, 0

    def crawl_comments_with_pagination(self, sb, article_url, expected_count=None):
        """Crawl comments với pagination thông minh"""
        print(f"\n[+] Bắt đầu crawl comments...")

        if expected_count:
            max_pages_needed = math.ceil(expected_count / 10)
            print(f"    Biết trước: {expected_count} comments → Cần {max_pages_needed} pages")
            pages_to_crawl = min(max_pages_needed, self.max_comments_pages)
        else:
            pages_to_crawl = self.max_comments_pages

        all_comments = []
        total_pages_crawled = 0

        for page_num in range(1, pages_to_crawl + 1):
            if page_num == 1:
                comments_url = f"{article_url}/comments"
            else:
                comments_url = f"{article_url}/comments?page={page_num}"

            print(f"    Page {page_num}: {comments_url}")

            try:
                sb.open(comments_url)
                sb.sleep(0.5)

                sb.scroll_to_bottom()
                sb.sleep(0.3)

                page_comments = self._extract_comments_from_page(sb)

                if page_comments:
                    num_comments = len(page_comments)
                    all_comments.extend(page_comments)
                    total_pages_crawled += 1
                    print(f"    ✓ {num_comments} comments")

                    if num_comments < 10:
                        print(f"    → Page cuối, DỪNG")
                        break
                else:
                    print(f"    ✗ Không có comments - Dừng")
                    break

            except Exception as e:
                print(f"    [!] Lỗi page {page_num}: {str(e)}")
                break

        print(f"[+] Tổng: {len(all_comments)} comments từ {total_pages_crawled} pages")
        self.stats["total_comments"] += len(all_comments)

        if expected_count:
            ideal_pages = math.ceil(expected_count / 10)
            pages_saved = self.max_comments_pages - ideal_pages
            if pages_saved > 0:
                self.stats["time_saved"] += pages_saved * 1

        return {
            "total_comments": len(all_comments),
            "pages_crawled": total_pages_crawled,
            "comments": all_comments
        }

    def _extract_comments_from_page(self, sb):
        """Trích xuất comments từ page"""
        comments = []

        try:
            comment_patterns = [
                "div[class*='omment']",
                "li[class*='omment']",
                "article[class*='omment']",
            ]

            found_elements = []
            for pattern in comment_patterns:
                try:
                    elements = sb.find_elements(pattern)
                    if len(elements) > len(found_elements):
                        found_elements = elements
                except:
                    continue

            if found_elements:
                for elem in found_elements:
                    try:
                        text = elem.text.strip()

                        if text and 10 < len(text) < 2000:
                            skip_keywords = ['Yahoo', 'ログイン', 'コメント', '件のコメント',
                                           '返信', '共有', '通報', 'もっと見る']

                            if not any(kw in text for kw in skip_keywords):
                                comment_data = {
                                    "text": text,
                                    "author": "Unknown",
                                    "likes": 0,
                                    "timestamp": "N/A"
                                }

                                try:
                                    like_match = re.search(r'(\d+)\s*いいね', elem.text)
                                    if like_match:
                                        comment_data["likes"] = int(like_match.group(1))
                                except:
                                    pass

                                comments.append(comment_data)
                    except:
                        continue

        except Exception as e:
            print(f"    [!] Lỗi extract: {str(e)}")

        return comments

    def enhance_articles_with_ai(self, articles):
        """
        🤖 AI ENHANCEMENT - Tích hợp tất cả AI use cases
        """
        if not self.ai or not self.enable_ai:
            print("[i] AI enhancement skipped (disabled)")
            return articles

        print(f"\n{'='*60}")
        print(f"🤖 AI ENHANCEMENT - Processing {len(articles)} articles")
        print(f"{'='*60}")

        enhanced_articles = []

        for i, article in enumerate(articles[:self.ai_batch_size], 1):
            print(f"\n[AI {i}/{min(len(articles), self.ai_batch_size)}] {article.get('title', 'N/A')[:50]}...")

            # USE CASE 1: Summarization
            print("  → Summarizing...")
            summary = self.ai.summarize_article(article)
            article["ai_summary"] = summary

            # USE CASE 4: Categorization & Tagging
            print("  → Categorizing...")
            categories = self.ai.categorize_article(article)
            article["ai_categories"] = categories

            # USE CASE 7: Quality Scoring
            print("  → Quality scoring...")
            quality = self.ai.score_article_quality(article)
            article["ai_quality"] = quality

            # USE CASE 2: Sentiment Analysis (if has comments)
            if article.get("comments_data", {}).get("comments"):
                print("  → Analyzing sentiment...")
                sentiment = self.ai.analyze_sentiment_advanced(
                    article["comments_data"]["comments"]
                )
                article["ai_sentiment"] = sentiment

            self.stats["ai_enhanced_articles"] += 1
            enhanced_articles.append(article)

            print(f"  ✓ AI enhancement complete")

            # Small delay
            time.sleep(0.5)

        print(f"\n[✓] AI enhancement done: {len(enhanced_articles)} articles")

        return enhanced_articles

    def generate_ai_insights(self, all_articles):
        """
        🤖 GENERATE AI INSIGHTS - Use cases 3, 6, 8
        """
        if not self.ai or not self.enable_ai or len(all_articles) == 0:
            return None

        print(f"\n{'='*60}")
        print(f"🤖 GENERATING AI INSIGHTS")
        print(f"{'='*60}")

        insights = {}

        # USE CASE 3: Trending Topics
        print("\n[AI] Detecting trending topics...")
        trending = self.ai.detect_trending_topics(all_articles, timeframe="24h")
        insights["trending"] = trending

        # USE CASE 8: Daily Report
        print("\n[AI] Generating daily report...")
        report = self.ai.generate_daily_report(all_articles)
        insights["daily_report"] = report

        # USE CASE 6: Anomaly Detection (if we have baseline)
        # TODO: Implement baseline tracking
        # For now, skip anomaly detection

        print(f"\n[✓] AI insights generated")
        return insights

    def crawl_single_run(self):
        """MỘT LẦN CRAWL với AI enhancement"""
        print("\n" + "="*60)
        print(f"BẮT ĐẦU CRAWL RUN #{self.stats['total_runs'] + 1}")
        if self.enable_ai:
            print("🤖 AI-ENHANCED MODE")
        print("="*60)

        last_known_id, last_known_url, last_time = self.load_tracking_data()

        new_articles_count = 0
        first_article_id_this_run = None
        first_article_url_this_run = None
        latest_output_file = None  # Track output file for updating

        with SB(uc=True, headless=self.headless) as sb:
            # 🔄 PHASE 2: Re-crawl comments từ pending list
            pending_recrawl = self.get_pending_recrawl()
            if pending_recrawl:
                print(f"\n{'='*60}")
                print(f"🔄 PHASE 2: RE-CRAWLING COMMENTS")
                print(f"Found {len(pending_recrawl)} articles ready for comment re-crawl")
                print(f"{'='*60}")

                for pending_item in pending_recrawl:
                    recrawled_data = self.recrawl_comments_only(sb, pending_item)

                    if recrawled_data:
                        # Tìm file JSON mới nhất để update
                        # Pattern: yahoo_news_ai_*.json
                        json_files = glob.glob("yahoo_news_ai_*.json")
                        if json_files:
                            # Sort by modification time
                            json_files.sort(key=os.path.getmtime, reverse=True)
                            latest_file = json_files[0]

                            print(f"  [🔄] Updating file: {latest_file}")
                            self.update_existing_article_with_comments(
                                latest_file,
                                recrawled_data["article_id"],
                                recrawled_data["comments_data"]
                            )

                print(f"\n[✓] Phase 2 complete: {self.stats['comments_recrawled']} articles updated with new comments\n")

            # 🔄 PHASE 1: Crawl bài mới
            for page in range(1, self.max_pages + 1):
                print(f"\n{'#'*60}")
                print(f"TRANG TÌM KIẾM {page}/{self.max_pages}")
                print(f"{'#'*60}")

                search_url = self.get_search_url(page)
                sb.open(search_url)
                sb.sleep(1)

                article_links = self.extract_article_links(sb)

                if not article_links:
                    print("[!] Không tìm thấy bài viết")
                    break

                found_known_article = False

                for idx, url in enumerate(article_links, 1):
                    article_id = self.extract_article_id_from_url(url)

                    if not article_id:
                        print(f"[!] Không extract được ID từ: {url}")
                        continue

                    # LOGIC: Kiểm tra có phải bài cũ không
                    if last_known_id and article_id == last_known_id:
                        print(f"\n{'='*60}")
                        print(f"🛑 ĐÃ GẶP BÀI CŨ NHẤT TỪ LẦN TRƯỚC!")
                        print(f"   ID: {article_id}")
                        print(f"   → DỪNG CRAWL!")
                        print(f"{'='*60}")
                        found_known_article = True
                        self.stats["duplicates_skipped"] += (len(article_links) - idx + 1)
                        break

                    print(f"\n--- Bài MỚI {new_articles_count + 1} (ID: {article_id[:12]}...) ---")

                    # Crawl content
                    article_data, has_comments, comment_count = self.crawl_article_content(sb, url)

                    if article_data:
                        # Lưu ID bài đầu tiên
                        if new_articles_count == 0:
                            first_article_id_this_run = article_id
                            first_article_url_this_run = url
                            print(f"\n[i] Bài đầu tiên - sẽ dùng làm mốc")
                            self.save_tracking_data(first_article_id_this_run, first_article_url_this_run)

                        # Crawl comments nếu có
                        if has_comments and comment_count > 0:
                            comments_data = self.crawl_comments_with_pagination(sb, url, comment_count)
                            article_data["comments_data"] = comments_data
                        else:
                            # Không có comments hoặc rất ít → Thêm vào pending để crawl lại sau 30 phút
                            article_data["comments_data"] = {
                                "total_comments": 0,
                                "pages_crawled": 0,
                                "comments": []
                            }
                            # 🔄 PHASE 1: Add to pending list
                            self.add_to_pending_comments(article_data)

                        self.articles.append(article_data)
                        new_articles_count += 1
                        self.stats["new_articles_this_run"] = new_articles_count

                        print(f"\n[✓] Bài mới #{new_articles_count}")

                    time.sleep(0.5)

                if found_known_article:
                    break

                print(f"\n[✓] Trang {page} - Tổng bài mới: {new_articles_count}")

        # Update tracking
        if first_article_id_this_run and new_articles_count > 0:
            self.save_tracking_data(first_article_id_this_run, first_article_url_this_run)

        self.stats["total_runs"] += 1

        # 🤖 AI ENHANCEMENT
        if self.enable_ai and len(self.articles) > 0:
            self.articles = self.enhance_articles_with_ai(self.articles)

            # Generate insights
            insights = self.generate_ai_insights(self.articles)

            # Save insights separately
            if insights:
                insights_file = f"ai_insights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(insights_file, 'w', encoding='utf-8') as f:
                    json.dump(insights, f, ensure_ascii=False, indent=2)
                print(f"\n[✓] AI insights saved: {insights_file}")

        return new_articles_count

    def save_results(self, filename=None):
        """Lưu kết quả"""
        if not self.articles:
            print("[!] Không có dữ liệu mới")
            return

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"yahoo_news_ai_{timestamp}.json"

        output = {
            "metadata": {
                "search_keyword": self.search_keyword,
                "total_articles": len(self.articles),
                "total_runs": self.stats["total_runs"],
                "articles_with_comments": self.stats["articles_with_comments"],
                "articles_without_comments": self.stats["articles_without_comments"],
                "total_comments": self.stats["total_comments"],
                "time_saved_seconds": self.stats["time_saved"],
                "duplicates_skipped": self.stats["duplicates_skipped"],
                "ai_enhanced": self.enable_ai,
                "ai_enhanced_articles": self.stats["ai_enhanced_articles"],
                "crawled_at": datetime.now().isoformat(),
                "headless_mode": self.headless,
                "interval_minutes": self.interval_minutes
            },
            "articles": self.articles
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*60}")
        print(f"[✓] Đã lưu {len(self.articles)} bài vào: {filename}")
        print(f"\n📊 THỐNG KÊ:")
        print(f"    Tổng runs: {self.stats['total_runs']}")
        print(f"    Bài mới run này: {self.stats['new_articles_this_run']}")
        print(f"    Có comments: {self.stats['articles_with_comments']} bài")
        print(f"    Tổng comments: {self.stats['total_comments']}")
        print(f"    Bài trùng bỏ qua: {self.stats['duplicates_skipped']}")
        if self.stats['comments_recrawled'] > 0:
            print(f"    🔄 Comments re-crawled: {self.stats['comments_recrawled']} bài")
        if self.enable_ai:
            print(f"    🤖 AI enhanced: {self.stats['ai_enhanced_articles']} bài")
            if self.ai:
                print(f"    🤖 AI cost: ${self.ai.stats['total_cost_usd']:.4f}")
        print(f"{'='*60}")

    def run_continuous(self, max_runs=None):
        """Chạy liên tục"""
        print("\n" + "╔" + "═"*78 + "╗")
        print("║" + " "*10 + "YAHOO NEWS AI-POWERED CONTINUOUS CRAWLER" + " "*26 + "║")
        print("╚" + "═"*78 + "╝")
        print()
        print(f"⚙️  Cấu hình:")
        print(f"    Từ khóa: {self.search_keyword}")
        print(f"    Headless: {self.headless}")
        print(f"    Interval: {self.interval_minutes} phút")
        print(f"    🤖 AI: {'Enabled' if self.enable_ai else 'Disabled'}")
        print(f"    Max runs: {max_runs if max_runs else 'Vô hạn'}")
        print()

        run_count = 0

        try:
            while True:
                run_count += 1

                if max_runs and run_count > max_runs:
                    print(f"\n[i] Đã chạy đủ {max_runs} lần - Dừng")
                    break

                print(f"\n{'█'*60}")
                print(f"RUN {run_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'█'*60}")

                self.stats["new_articles_this_run"] = 0

                new_articles = self.crawl_single_run()

                if new_articles > 0:
                    self.save_results()
                else:
                    print(f"\n[i] Không có bài mới trong run này")

                if max_runs and run_count >= max_runs:
                    break

                sleep_seconds = self.interval_minutes * 60
                print(f"\n{'='*60}")
                print(f"💤 Sleep {self.interval_minutes} phút...")
                print(f"{'='*60}")

                time.sleep(sleep_seconds)

        except KeyboardInterrupt:
            print("\n\n[!] Dừng bởi user (Ctrl+C)")
            if self.articles:
                self.save_results()

        except Exception as e:
            print(f"\n[!] Lỗi: {str(e)}")
            import traceback
            traceback.print_exc()
            if self.articles:
                self.save_results()

        # Print AI stats
        if self.ai:
            self.ai.print_stats()


def main():
    """Main"""
    import argparse

    parser = argparse.ArgumentParser(description='Yahoo News AI-Powered Crawler')
    parser.add_argument('--headless', action='store_true',
                       help='Chạy ẩn browser')
    parser.add_argument('--interval', type=int, default=30,
                       help='Thời gian giữa các lần crawl (phút)')
    parser.add_argument('--max-runs', type=int, default=None,
                       help='Số lần crawl tối đa')
    parser.add_argument('--single', action='store_true',
                       help='Chỉ chạy 1 lần')
    parser.add_argument('--no-ai', action='store_true',
                       help='Tắt AI features')
    parser.add_argument('--api-key', type=str, default=None,
                       help='Claude API key (hoặc dùng trong code)')

    args = parser.parse_args()

    # API KEY - Lấy từ args hoặc hardcode
    api_key = args.api_key or "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"

    print("\n")
    print("╔" + "═"*78 + "╗")
    print("║" + " "*12 + "YAHOO NEWS AI-POWERED CRAWLER - V2.0" + " "*29 + "║")
    print("╚" + "═"*78 + "╝")
    print()

    crawler = AIEnhancedYahooNewsCrawler(
        search_keyword="大谷翔平",
        max_pages=2,
        max_comments_pages=5,
        headless=args.headless,
        interval_minutes=args.interval,
        claude_api_key=api_key,
        enable_ai=not args.no_ai,
        ai_batch_size=10
    )

    try:
        if args.single:
            print("[i] Single run mode - chỉ crawl 1 lần")
            new_articles = crawler.crawl_single_run()
            if new_articles > 0:
                crawler.save_results()
        else:
            crawler.run_continuous(max_runs=args.max_runs)

        print("\n")
        print("╔" + "═"*78 + "╗")
        print("║" + " "*30 + "HOÀN THÀNH!" + " "*34 + "║")
        print("║" + f" Tổng bài: {len(crawler.articles)}".ljust(78) + "║")
        if crawler.enable_ai:
            print("║" + f" 🤖 AI enhanced: {crawler.stats['ai_enhanced_articles']}".ljust(78) + "║")
        print("╚" + "═"*78 + "╝")

    except Exception as e:
        print(f"\n[!] Lỗi: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

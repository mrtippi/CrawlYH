"""
CLAUDE AI ANALYZER - Yahoo News Intelligence Layer
==================================================

Tích hợp Claude AI API để phân tích sâu dữ liệu crawl:
1. Summarization - Tóm tắt bài viết
2. Sentiment Analysis - Phân tích cảm xúc comments
3. Trending Topics - Phát hiện xu hướng
4. Auto-categorization - Tự động phân loại
5. Q&A System - Hỏi đáp thông minh
6. Anomaly Detection - Phát hiện bất thường
7. Quality Scoring - Đánh giá chất lượng
8. Daily Reports - Báo cáo tự động
"""

import sys
import os

# Fix Unicode encoding cho Windows console
if sys.platform == 'win32':
    try:
        import codecs
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass  # Already wrapped or not needed

import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import anthropic
import time


class ClaudeAnalyzer:
    """Claude AI Analyzer - Brain của Yahoo News Crawler"""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        """
        Khởi tạo Claude AI client

        Args:
            api_key: Claude API key
            model: Model to use (haiku=cheap, sonnet=balanced, opus=powerful)
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

        # Stats tracking
        self.stats = {
            "total_api_calls": 0,
            "total_tokens_used": 0,
            "total_cost_usd": 0.0,
            "calls_by_feature": {}
        }

    def _call_claude(self, prompt: str, max_tokens: int = 2000,
                     feature_name: str = "general") -> str:
        """
        Internal method to call Claude API

        Args:
            prompt: Prompt to send
            max_tokens: Max response tokens
            feature_name: Feature name for tracking

        Returns:
            Claude's response text
        """
        try:
            print(f"[Claude AI] Calling {feature_name}...")

            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract response text
            response_text = response.content[0].text

            # Track stats
            self.stats["total_api_calls"] += 1
            self.stats["total_tokens_used"] += response.usage.input_tokens + response.usage.output_tokens

            # Track by feature
            if feature_name not in self.stats["calls_by_feature"]:
                self.stats["calls_by_feature"][feature_name] = 0
            self.stats["calls_by_feature"][feature_name] += 1

            # Estimate cost (Sonnet pricing: $3/M input, $15/M output)
            input_cost = (response.usage.input_tokens / 1_000_000) * 3
            output_cost = (response.usage.output_tokens / 1_000_000) * 15
            self.stats["total_cost_usd"] += (input_cost + output_cost)

            print(f"[✓] {feature_name} completed (tokens: {response.usage.input_tokens + response.usage.output_tokens})")

            return response_text

        except Exception as e:
            print(f"[!] Claude API error: {str(e)}")
            return None

    # ═══════════════════════════════════════════════════════════════
    # USE CASE 1: ARTICLE SUMMARIZATION
    # ═══════════════════════════════════════════════════════════════

    def summarize_article(self, article: Dict) -> Dict:
        """
        Tóm tắt bài viết thành 2-3 câu ngắn gọn

        Args:
            article: Dict containing title, content, url

        Returns:
            Dict with summary and key_points
        """
        title = article.get("title", "N/A")
        content = article.get("content", "N/A")

        if content == "N/A" or len(content) < 50:
            return {
                "summary": "Không đủ nội dung để tóm tắt",
                "key_points": [],
                "error": "Insufficient content"
            }

        prompt = f"""Bạn là chuyên gia phân tích tin tức thể thao Nhật Bản.

Bài viết:
Tiêu đề: {title}
Nội dung: {content[:2000]}

Nhiệm vụ:
1. Tóm tắt bài viết thành 2-3 câu TIẾNG VIỆT, ngắn gọn, súc tích
2. Liệt kê 3-5 điểm chính (key points) bằng TIẾNG VIỆT

Trả lời theo format JSON:
{{
  "summary": "Tóm tắt 2-3 câu tiếng Việt",
  "key_points": ["Điểm 1", "Điểm 2", "Điểm 3"]
}}

Chỉ trả về JSON, không thêm text khác."""

        response = self._call_claude(prompt, max_tokens=500, feature_name="summarization")

        if response:
            try:
                # Parse JSON response
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                # Fallback if not valid JSON
                return {
                    "summary": response[:300],
                    "key_points": [],
                    "raw_response": response
                }
        else:
            return {
                "summary": "Lỗi khi tóm tắt",
                "key_points": [],
                "error": "API call failed"
            }

    def summarize_batch(self, articles: List[Dict], max_articles: int = 50) -> List[Dict]:
        """
        Tóm tắt nhiều bài viết cùng lúc (batch processing - tiết kiệm cost)

        Args:
            articles: List of article dicts
            max_articles: Max articles to process in one batch

        Returns:
            List of articles with summaries added
        """
        print(f"\n[Claude AI] Batch summarization: {len(articles)} articles")

        results = []
        for i, article in enumerate(articles[:max_articles], 1):
            print(f"  Processing {i}/{min(len(articles), max_articles)}...")
            summary_data = self.summarize_article(article)

            # Add summary to article
            article["ai_summary"] = summary_data
            results.append(article)

            # Small delay to avoid rate limits
            time.sleep(0.5)

        return results

    # ═══════════════════════════════════════════════════════════════
    # USE CASE 2: ADVANCED SENTIMENT ANALYSIS
    # ═══════════════════════════════════════════════════════════════

    def analyze_sentiment_advanced(self, comments: List[Dict]) -> Dict:
        """
        Phân tích sentiment của comments một cách thông minh

        Args:
            comments: List of comment dicts with 'text' field

        Returns:
            Dict with detailed sentiment analysis
        """
        if not comments or len(comments) == 0:
            return {
                "overall_sentiment": "neutral",
                "sentiment_breakdown": {},
                "key_emotions": [],
                "error": "No comments to analyze"
            }

        # Get sample comments (max 50 for cost efficiency)
        sample_comments = comments[:50]
        comments_text = "\n".join([f"- {c.get('text', '')[:200]}" for c in sample_comments])

        prompt = f"""Bạn là chuyên gia phân tích cảm xúc (sentiment analysis) cho comments tiếng Nhật.

Có {len(comments)} comments, đây là mẫu {len(sample_comments)} comments:

{comments_text}

Nhiệm vụ:
1. Phân tích OVERALL SENTIMENT (positive/negative/mixed/neutral)
2. Breakdown theo %: positive, negative, neutral
3. Identify TOP EMOTIONS (ví dụ: excited, worried, proud, angry, hopeful)
4. Phát hiện MAIN CONCERNS nếu có
5. Tóm tắt GENERAL TONE bằng 1 câu tiếng Việt

Trả lời theo JSON format:
{{
  "overall_sentiment": "positive/negative/mixed/neutral",
  "sentiment_breakdown": {{"positive": 67, "negative": 23, "neutral": 10}},
  "top_emotions": ["excited", "proud", "hopeful"],
  "main_concerns": ["injury risk", "contract"],
  "general_tone": "Tóm tắt chung 1 câu tiếng Việt",
  "confidence": 0.85
}}

Chỉ trả về JSON."""

        response = self._call_claude(prompt, max_tokens=600, feature_name="sentiment_analysis")

        if response:
            try:
                result = json.loads(response)
                result["total_comments_analyzed"] = len(sample_comments)
                result["total_comments"] = len(comments)
                return result
            except json.JSONDecodeError:
                return {
                    "overall_sentiment": "unknown",
                    "error": "Failed to parse response",
                    "raw_response": response
                }
        else:
            return {
                "overall_sentiment": "error",
                "error": "API call failed"
            }

    # ═══════════════════════════════════════════════════════════════
    # USE CASE 3: TRENDING TOPICS & INSIGHTS
    # ═══════════════════════════════════════════════════════════════

    def detect_trending_topics(self, articles: List[Dict], timeframe: str = "24h") -> Dict:
        """
        Phát hiện trending topics và insights từ nhiều bài viết

        Args:
            articles: List of articles
            timeframe: Time period (24h, 7d, 30d)

        Returns:
            Dict with trending topics and insights
        """
        if not articles or len(articles) == 0:
            return {
                "trending_topics": [],
                "insights": [],
                "error": "No articles to analyze"
            }

        # Extract titles and summaries
        titles = [a.get("title", "") for a in articles[:100]]
        titles_text = "\n".join([f"- {t}" for t in titles])

        # Count comments and dates
        total_comments = sum([a.get("comments_data", {}).get("total_comments", 0) for a in articles])
        avg_comments = total_comments / len(articles) if len(articles) > 0 else 0

        prompt = f"""Bạn là data analyst chuyên về tin tức thể thao Nhật Bản.

Phân tích {len(articles)} bài viết trong {timeframe} gần đây về Ohtani Shohei:

Titles:
{titles_text}

Stats:
- Total articles: {len(articles)}
- Total comments: {total_comments}
- Avg comments/article: {avg_comments:.1f}

Nhiệm vụ:
1. Identify TOP 5 TRENDING TOPICS (chủ đề hot nhất)
2. Detect RISING TRENDS (xu hướng đang tăng)
3. Generate KEY INSIGHTS (phát hiện quan trọng)
4. Predict WHAT'S NEXT (dự đoán xu hướng tiếp theo)

Format JSON:
{{
  "trending_topics": [
    {{"topic": "World Series", "mentions": 67, "trend": "rising", "importance": "high"}},
    {{"topic": "MVP Race", "mentions": 45, "trend": "stable", "importance": "high"}}
  ],
  "rising_trends": ["Contract talks", "Injury concern"],
  "key_insights": [
    "67% articles focus on World Series preparation",
    "Spike in injury-related coverage (+340%)"
  ],
  "predictions": ["MVP announcement next week", "Off-season contract news"],
  "summary_vietnamese": "Tóm tắt tổng quan 2-3 câu tiếng Việt"
}}

Chỉ trả về JSON."""

        response = self._call_claude(prompt, max_tokens=800, feature_name="trending_detection")

        if response:
            try:
                result = json.loads(response)
                result["analyzed_articles"] = len(articles)
                result["timeframe"] = timeframe
                result["analysis_timestamp"] = datetime.now().isoformat()
                return result
            except json.JSONDecodeError:
                return {
                    "trending_topics": [],
                    "error": "Failed to parse response",
                    "raw_response": response
                }
        else:
            return {
                "trending_topics": [],
                "error": "API call failed"
            }

    # ═══════════════════════════════════════════════════════════════
    # USE CASE 4: AUTO-CATEGORIZATION & TAGGING
    # ═══════════════════════════════════════════════════════════════

    def categorize_article(self, article: Dict) -> Dict:
        """
        Tự động phân loại bài viết và gắn tags

        Args:
            article: Article dict

        Returns:
            Dict with categories, tags, type, importance
        """
        title = article.get("title", "N/A")
        content = article.get("content", "N/A")[:1000]

        prompt = f"""Bạn là hệ thống phân loại tin tức thông minh.

Bài viết:
Title: {title}
Content: {content}

Nhiệm vụ: Phân loại bài viết này

Categories (chọn 1-2):
- Performance (thành tích thi đấu)
- Health/Injury (sức khỏe, chấn thương)
- Business (hợp đồng, thương mại)
- Personal (đời tư)
- Team News (tin đội)
- Records (kỷ lục)
- Training (tập luyện)

Tags (chọn 2-5):
- Home Run, Batting, Pitching, Defense
- MVP, World Series, Playoff
- Injury, Recovery, Surgery
- Contract, Salary, Endorsement
- Record Breaking, Milestone
- etc.

Article Type:
- Game Recap, Preview, Analysis
- Breaking News, Update
- Interview, Feature
- Opinion, Commentary

Importance:
- Critical (breaking news, major records)
- High (important games, significant news)
- Medium (regular updates)
- Low (minor news, routine)

Format JSON:
{{
  "categories": ["Performance", "Records"],
  "tags": ["Home Run", "MVP Race", "Record Breaking"],
  "article_type": "Breaking News",
  "importance": "high",
  "reasoning": "Giải thích ngắn gọn tại sao phân loại như vậy"
}}

Chỉ trả về JSON."""

        response = self._call_claude(prompt, max_tokens=400, feature_name="categorization")

        if response:
            try:
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                return {
                    "categories": ["Uncategorized"],
                    "tags": [],
                    "article_type": "Unknown",
                    "importance": "medium",
                    "error": "Failed to parse response"
                }
        else:
            return {
                "categories": ["Error"],
                "tags": [],
                "error": "API call failed"
            }

    # ═══════════════════════════════════════════════════════════════
    # USE CASE 5: Q&A SYSTEM (RAG - Retrieval-Augmented Generation)
    # ═══════════════════════════════════════════════════════════════

    def answer_question(self, question: str, articles: List[Dict],
                       max_context_articles: int = 10) -> Dict:
        """
        Trả lời câu hỏi dựa trên dữ liệu đã crawl (RAG)

        Args:
            question: User's question
            articles: List of relevant articles (pre-filtered or all)
            max_context_articles: Max articles to include in context

        Returns:
            Dict with answer, sources, confidence
        """
        if not articles:
            return {
                "answer": "Không có dữ liệu để trả lời câu hỏi này.",
                "sources": [],
                "confidence": 0.0
            }

        # Build context from articles
        context_articles = articles[:max_context_articles]
        context_text = ""

        for i, article in enumerate(context_articles, 1):
            title = article.get("title", "N/A")
            content = article.get("content", "N/A")[:500]
            url = article.get("url", "N/A")
            date = article.get("published_date", "N/A")

            context_text += f"\n[Article {i}]\nTitle: {title}\nDate: {date}\nContent: {content}\nURL: {url}\n"

        prompt = f"""Bạn là AI assistant chuyên về tin tức Ohtani Shohei.

User hỏi: "{question}"

Context (dữ liệu đã crawl):
{context_text}

Nhiệm vụ:
1. Trả lời câu hỏi dựa trên CONTEXT PROVIDED (không bịa đặt)
2. Nếu không có thông tin → nói rõ "Không có thông tin trong dữ liệu"
3. Cite sources (Article [1], [2]...)
4. Trả lời bằng TIẾNG VIỆT, rõ ràng, súc tích

Format JSON:
{{
  "answer": "Câu trả lời chi tiết bằng tiếng Việt",
  "sources": ["Article 1", "Article 3"],
  "confidence": 0.85,
  "related_topics": ["World Series", "MVP"]
}}

Chỉ trả về JSON."""

        response = self._call_claude(prompt, max_tokens=600, feature_name="qa_system")

        if response:
            try:
                result = json.loads(response)
                # Add URLs for cited sources
                cited_indices = []
                for source in result.get("sources", []):
                    try:
                        idx = int(source.replace("Article", "").strip()) - 1
                        if 0 <= idx < len(context_articles):
                            cited_indices.append(idx)
                    except:
                        pass

                result["source_urls"] = [context_articles[i].get("url") for i in cited_indices]
                result["context_articles_count"] = len(context_articles)

                return result
            except json.JSONDecodeError:
                return {
                    "answer": response,
                    "sources": [],
                    "confidence": 0.5,
                    "error": "Failed to parse JSON"
                }
        else:
            return {
                "answer": "Lỗi khi gọi Claude API",
                "sources": [],
                "confidence": 0.0,
                "error": "API call failed"
            }

    # ═══════════════════════════════════════════════════════════════
    # USE CASE 6: ANOMALY DETECTION
    # ═══════════════════════════════════════════════════════════════

    def detect_anomalies(self, current_stats: Dict, historical_baseline: Dict) -> Dict:
        """
        Phát hiện bất thường trong patterns crawl

        Args:
            current_stats: Current period stats
            historical_baseline: Normal baseline stats

        Returns:
            Dict with anomalies detected and alerts
        """
        prompt = f"""Bạn là hệ thống anomaly detection cho news monitoring.

BASELINE (Normal):
- Articles/hour: {historical_baseline.get('articles_per_hour', 15)}
- Comments/article: {historical_baseline.get('comments_per_article', 12)}
- Sentiment: {historical_baseline.get('sentiment', 'mixed')}

CURRENT:
- Articles/hour: {current_stats.get('articles_per_hour', 0)}
- Comments/article: {current_stats.get('comments_per_article', 0)}
- Sentiment: {current_stats.get('sentiment', 'unknown')}

Nhiệm vụ:
1. Detect ANOMALIES (bất thường so với baseline)
2. Classify severity: critical/high/medium/low
3. Suggest possible reasons
4. Recommend actions

Format JSON:
{{
  "anomalies_detected": true/false,
  "alerts": [
    {{
      "type": "volume_spike",
      "severity": "high",
      "description": "Article volume 340% above normal",
      "possible_reasons": ["Breaking news", "Major event"],
      "recommended_actions": ["Increase crawl frequency", "Alert admin"]
    }}
  ],
  "summary_vietnamese": "Tóm tắt tình hình"
}}

Chỉ trả về JSON."""

        response = self._call_claude(prompt, max_tokens=500, feature_name="anomaly_detection")

        if response:
            try:
                result = json.loads(response)
                result["detection_timestamp"] = datetime.now().isoformat()
                return result
            except json.JSONDecodeError:
                return {
                    "anomalies_detected": False,
                    "error": "Failed to parse response"
                }
        else:
            return {
                "anomalies_detected": False,
                "error": "API call failed"
            }

    # ═══════════════════════════════════════════════════════════════
    # USE CASE 7: CONTENT QUALITY SCORING
    # ═══════════════════════════════════════════════════════════════

    def score_article_quality(self, article: Dict) -> Dict:
        """
        Đánh giá chất lượng bài viết

        Args:
            article: Article dict

        Returns:
            Dict with quality score and analysis
        """
        title = article.get("title", "N/A")
        content = article.get("content", "N/A")[:1500]
        source = article.get("source", "N/A")
        has_comments = article.get("has_comments", False)
        comment_count = article.get("estimated_comment_count", 0)

        prompt = f"""Bạn là chuyên gia đánh giá chất lượng nội dung tin tức.

Bài viết:
Title: {title}
Source: {source}
Content length: {len(content)} chars
Comments: {comment_count}
Content: {content}

Criteria đánh giá (0-10 scale):
1. Credibility (độ tin cậy): có sources/quotes/data?
2. Depth (độ sâu): phân tích hay chỉ surface?
3. Objectivity (khách quan): balanced hay bias?
4. Relevance (liên quan): quan trọng với readers?
5. Writing Quality (chất lượng viết): clear/engaging?

Overall Score: 0-10

Format JSON:
{{
  "overall_score": 8.5,
  "scores": {{
    "credibility": 9,
    "depth": 8,
    "objectivity": 8,
    "relevance": 9,
    "writing_quality": 8
  }},
  "quality_tier": "high/medium/low",
  "strengths": ["Strong data backing", "Expert quotes"],
  "weaknesses": ["Lacks historical context"],
  "recommendation": "Feature on homepage / Archive / Skip",
  "reasoning": "Giải thích ngắn gọn"
}}

Chỉ trả về JSON."""

        response = self._call_claude(prompt, max_tokens=500, feature_name="quality_scoring")

        if response:
            try:
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                return {
                    "overall_score": 5.0,
                    "quality_tier": "medium",
                    "error": "Failed to parse response"
                }
        else:
            return {
                "overall_score": 0.0,
                "quality_tier": "unknown",
                "error": "API call failed"
            }

    # ═══════════════════════════════════════════════════════════════
    # USE CASE 8: AUTO-GENERATE DAILY REPORTS
    # ═══════════════════════════════════════════════════════════════

    def generate_daily_report(self, articles: List[Dict],
                             date: str = None) -> Dict:
        """
        Tạo báo cáo tự động hàng ngày

        Args:
            articles: All articles from the day
            date: Report date (default: today)

        Returns:
            Dict with comprehensive daily report
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        if not articles:
            return {
                "date": date,
                "report": "Không có dữ liệu cho ngày này",
                "error": "No articles"
            }

        # Aggregate stats
        total_articles = len(articles)
        total_comments = sum([a.get("comments_data", {}).get("total_comments", 0) for a in articles])

        # Get top articles
        articles_sorted = sorted(articles,
                                key=lambda x: x.get("comments_data", {}).get("total_comments", 0),
                                reverse=True)
        top_3_titles = [a.get("title", "N/A") for a in articles_sorted[:3]]

        # Build prompt
        titles_sample = "\n".join([f"- {a.get('title', 'N/A')}" for a in articles[:50]])

        prompt = f"""Bạn là AI journalist tạo báo cáo tin tức hàng ngày.

Date: {date}
Total articles: {total_articles}
Total comments: {total_comments}

Top articles:
{chr(10).join([f"{i+1}. {t}" for i, t in enumerate(top_3_titles)])}

Sample titles:
{titles_sample}

Nhiệm vụ: Tạo DAILY REPORT bằng TIẾNG VIỆT

Format báo cáo:
1. EXECUTIVE SUMMARY (2-3 câu tổng quan)
2. TOP STORIES (3 tin nổi bật)
3. KEY TRENDS (xu hướng chính)
4. FAN SENTIMENT (cảm xúc người hâm mộ)
5. OUTLOOK (dự báo)

Format JSON:
{{
  "date": "{date}",
  "executive_summary": "Tóm tắt ngắn gọn",
  "top_stories": [
    {{"title": "...", "summary": "...", "impact": "high/medium/low"}}
  ],
  "key_trends": ["Trend 1", "Trend 2"],
  "fan_sentiment": {{"overall": "positive", "description": "..."}},
  "outlook": "Dự báo cho ngày/tuần tới",
  "statistics": {{
    "total_articles": {total_articles},
    "total_comments": {total_comments},
    "avg_comments": {total_comments/max(total_articles, 1):.1f}
  }}
}}

Chỉ trả về JSON."""

        response = self._call_claude(prompt, max_tokens=1000, feature_name="daily_report")

        if response:
            try:
                result = json.loads(response)
                result["generated_at"] = datetime.now().isoformat()
                return result
            except json.JSONDecodeError:
                return {
                    "date": date,
                    "report_text": response,
                    "error": "Failed to parse JSON"
                }
        else:
            return {
                "date": date,
                "error": "API call failed"
            }

    # ═══════════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict:
        """Get usage statistics"""
        return self.stats

    def print_stats(self):
        """Print usage statistics"""
        print("\n" + "="*60)
        print("CLAUDE AI USAGE STATISTICS")
        print("="*60)
        print(f"Total API calls: {self.stats['total_api_calls']}")
        print(f"Total tokens used: {self.stats['total_tokens_used']:,}")
        print(f"Estimated cost: ${self.stats['total_cost_usd']:.4f}")
        print(f"\nCalls by feature:")
        for feature, count in self.stats['calls_by_feature'].items():
            print(f"  - {feature}: {count} calls")
        print("="*60)


def main():
    """Demo/Test function"""
    print("Claude AI Analyzer - Demo")
    print("="*60)

    # Initialize (YOU NEED TO SET YOUR API KEY)
    api_key = "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"

    analyzer = ClaudeAnalyzer(api_key=api_key)

    #change nothing

    # Test article
    test_article = {
        "title": "大谷翔平、54号ホームラン！3年ぶりの本塁打王",
        "content": "ドジャースの大谷翔平選手が、3年ぶりとなる本塁打王に輝いた。今シーズンは54本のホームランを記録し、チームの優勝にも大きく貢献した。",
        "url": "https://example.com/article1",
        "has_comments": True,
        "estimated_comment_count": 45
    }

    # Test 1: Summarization
    print("\n[TEST 1] Summarization")
    summary = analyzer.summarize_article(test_article)
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    # Test 2: Categorization
    print("\n[TEST 2] Categorization")
    categories = analyzer.categorize_article(test_article)
    print(json.dumps(categories, ensure_ascii=False, indent=2))

    # Print stats
    analyzer.print_stats()


if __name__ == "__main__":
    main()

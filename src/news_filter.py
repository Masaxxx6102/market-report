import json
import google.generativeai as genai
from typing import List, Dict, Any
from .config import settings
from .logger_setup import logger
from tenacity import retry, stop_after_attempt, wait_exponential

class NewsFilterAI:
    """
    Uses LLMs to filter and prioritize news items.
    """
    def __init__(self, gemini_key: str):
        genai.configure(api_key=gemini_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash') # Standard high-performance model (March 2026)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def filter_news(self, news_items: List[Dict[str, Any]], watchlist_symbols: List[str] = None) -> List[Dict[str, Any]]:
        """
        Send news items to Gemini for filtering and categorization.
        """
        if not news_items:
            return []

        watchlist_str = ", ".join(watchlist_symbols) if watchlist_symbols else "特に指定なし"

        # Prepare payload (taking a larger subset for more variety)
        # Gemini Flash can handle larger context easily (1M+ tokens)
        news_subset = news_items[:500]
        news_json = json.dumps(news_subset, ensure_ascii=False)
        
        prompt = f"""
【最優先事項】
各カテゴリ（マクロ、メガキャップ、決算、地政学）について、それぞれ「必ず10件ずつ」、合計で「40件程度」のニュースを必ず選出してください。
特定のカテゴリ（特にマクロ経済）に偏りすぎないよう、各ジャンルからバランス良く、最も市場にインパクトのあるものを厳選してください。

【厳守：決算・ガイダンス速報のフィルタリング】
「決算・ガイダンス速報」カテゴリについては、**必ず監視銘柄リスト（日米の主要企業約20社程度）に含まれる企業のみ**を選出してください。
それ以外の、リストに含まれないマイナーな個別企業の決算ニュースは、たとえ重要に見えても「除外」してください。
監視銘柄: {watchlist_str}

【優先順位】
1. **監視銘柄の動向**: 監視対象銘柄に関する決算や重要なニュース。
2. **マクロ経済・金融政策**: FRBや日銀の要人発言、金利動向、インフレ指標、雇用統計など。
3. **国際・地政学**: 戦争、紛争、地政学的リスク。
4. **メガキャップ・ムーブメント**: 時価総額の大きな企業の個別ニュース。

【フィルタリング・編集基準】
1. カテゴリ分類：
   - 【マクロ経済・金融政策】
   - 【メガキャップ・ムーブメント】
   - 【決算・ガイダンス速報】
   - 【国際・地政学】
2. 採用件数：各カテゴリ10件（合計40件）を**厳守**してください。
3. 要約：各ニュース日本語で「400〜500文字程度」でプロフェッショナルな深い解説を行ってください。
4. 翻訳：マーケット用語を正しく用いた自然で重厚な日本語へ。タイトル（Headline）も必ず日本語に翻訳してください。
5. **情報源（Source）**: 元のニュースサイト名（例: Reuters, Bloomberg, Yahoo Finance等）を必ず保持してください。

【出力形式】
必ず以下のJSON構造のみを返してください。
{{
  "selected_news": [
    {{
      "headline": "日本語のタイトル",
      "summary": "日本語の詳細な要約（400〜500字）",
      "category": "【カテゴリ名】",
      "importance": 10,
      "source": "元のソース名（Reuters等）",
      "url": "元のURLをそのまま保持",
      "related_symbols": ["AAPL", "TSLA"]
    }}
  ]
}}

ニュースデータ:
{news_json}
"""
        try:
            response = self.model.generate_content(prompt)
            # Find JSON in response
            text = response.text
            if "```json" in text:
                text = text.split("```json")[-1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[-1].split("```")[0].strip()
            
            result = json.loads(text)
            selected = result.get("selected_news", [])
            logger.info(f"AI selected {len(selected)} news items based on the new criteria.")
            return selected
        except Exception as e:
            logger.error(f"AI Filtering failed: {e}")
            # Fallback: Return top 15 news with raw data
            fallback_news = []
            for item in news_items[:15]:
                fallback_news.append({
                    "headline": item.get("headline") or "News Update",
                    "summary": (item.get("summary") or "")[:100] + "...",
                    "category": "General",
                    "importance": 5,
                    "source": item.get("source", "Unknown"),
                    "related_symbols": item.get("related_symbols", [])
                })
            return fallback_news
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate_market_overview(self, news_items: List[Dict[str, Any]], quotes: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate a deep dive market overview for US and JP markets (approx 1000 chars each).
        """
        news_json = json.dumps(news_items[:200], ensure_ascii=False)
        quotes_json = json.dumps(quotes, ensure_ascii=False)

        prompt = f"""
あなたはプロのシニア提携マーケットアナリストです。
提供された最新ニュースと市場価格データに基づき、日本市場と米国市場について、それぞれ「1000文字程度」の重厚な概況レポートを作成してください。

【構成要素】
1. **日本市場概況**: 昨日の値動き、背景にあるマクロ経済要因、日銀の動向、主要セクター（半導体、金融、自動車等）の動き、今後の展望。
2. **米国市場概況**: 昨晩の値動き、FRB要人発言や金利動向、主要経済指標の結果、メガキャップ株の動向、インフレや景気後退懸念に関する市場心理の分析。

【執筆スタイル】
- 投資家やプロのアナリストが読むことを想定した、論理的で格調高い日本語。
- 単なる事実（株価の上下）だけでなく、その背後にある深い構造的な要因や、市場参加者のセンチメントの変化を鋭く分析してください。
- 合計で2000文字以上のボリューム（各1000字目安）を厳守し、情報密度の高い内容にしてください。

【ニュース・価格データ】
指数・個別株価格: {quotes_json}
ニュース: {news_json}

【出力形式】
JSON形式で返してください。
{{
  "jp_overview": "日本市場の1000文字以上の概況テキスト...",
  "us_overview": "米国市場の1000文字以上の概況テキスト..."
}}
"""
        try:
            response = self.model.generate_content(prompt)
            text = response.text
            if "```json" in text:
                text = text.split("```json")[-1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[-1].split("```")[0].strip()
            
            result = json.loads(text)
            logger.info("Market overview generated successfully (approx 2000 chars total).")
            return result
        except Exception as e:
            logger.error(f"Failed to generate market overview: {e}")
            return {
                "jp_overview": "日本市場の概況生成に失敗しました。",
                "us_overview": "米国市場の概況生成に失敗しました。"
            }

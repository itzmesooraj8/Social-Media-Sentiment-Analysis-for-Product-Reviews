from typing import List, Dict, Any
from collections import defaultdict
import asyncio

from database import supabase

KEYWORD_ALERTS = ["fire", "broken", "scam"]


class MonitorService:
    async def evaluate_review(self, product_id: str, review: Dict[str, Any], sentiment_result: Dict[str, Any]):
        """
        Check a single review for alert conditions and insert into `alerts` if triggered.
        """
        try:
            score = float(sentiment_result.get("score", 0) or 0)
            text = (review.get("text") or "").lower()

            # Check for keywords
            has_keyword = any(k in text for k in KEYWORD_ALERTS)

            if score < 0.3 and has_keyword:
                message = f"Low sentiment ({score:.2f}) and flagged keywords found in review: {', '.join([k for k in KEYWORD_ALERTS if k in text])}"
                alert = {
                    "type": "sentiment_shift",
                    "message": message,
                    "severity": "high",
                    "is_read": False
                }
                try:
                    supabase.table("alerts").insert(alert).execute()
                except Exception as e:
                    print(f"Failed to insert alert: {e}")
        except Exception as e:
            print(f"Monitor evaluate_review error: {e}")

    async def extract_and_save_topics(self, product_id: str, reviews: List[Dict[str, Any]]):
        """
        Extract noun-phrases or high-value n-grams from reviews and save to `topic_clusters`.
        Falls back to CountVectorizer if NLTK is not available.
        """
        try:
            texts = [r.get("text", "") for r in reviews if r.get("text")]
            if not texts:
                return

            # Try NLTK-based noun phrase extraction
            topics = defaultdict(lambda: {"mentions": 0, "sentiments": []})
            try:
                import nltk
                from nltk import word_tokenize, pos_tag
                nltk.download('punkt', quiet=True)
                nltk.download('averaged_perceptron_tagger', quiet=True)

                for idx, text in enumerate(texts):
                    tokens = word_tokenize(text)
                    tags = pos_tag(tokens)
                    # simple NP extraction: consecutive nouns/adjectives
                    np = []
                    cur = []
                    for word, tag in tags:
                        if tag.startswith('NN') or tag.startswith('JJ'):
                            cur.append(word.lower())
                        else:
                            if cur:
                                np_name = ' '.join(cur)
                                topics[np_name]['mentions'] += 1
                                cur = []
                    if cur:
                        np_name = ' '.join(cur)
                        topics[np_name]['mentions'] += 1

            except Exception:
                # Fallback: use sklearn CountVectorizer
                try:
                    from sklearn.feature_extraction.text import CountVectorizer
                    vec = CountVectorizer(ngram_range=(1, 2), stop_words='english', max_features=50)
                    X = vec.fit_transform(texts)
                    sums = X.sum(axis=0)
                    terms = vec.get_feature_names_out()
                    for term, col in zip(terms, sums.tolist()[0]):
                        topics[term]['mentions'] = int(col)
                except Exception as e:
                    print(f"Topic extraction fallback failed: {e}")

            # Prepare rows
            rows = []
            for topic_name, data in topics.items():
                mention_count = int(data.get('mentions', 0))
                if mention_count <= 0:
                    continue
                # sentiment_score: approximate neutral (0.5) as we don't have mapping here
                sentiment_score = 0.5
                rows.append({
                    "product_id": product_id,
                    "topic_name": topic_name,
                    "sentiment_score": sentiment_score,
                    "mention_count": mention_count
                })

            if not rows:
                return

            # Remove existing clusters for product and insert new
            try:
                supabase.table('topic_clusters').delete().eq('product_id', product_id).execute()
            except Exception:
                pass

            try:
                # Insert in batches of 50
                for i in range(0, len(rows), 50):
                    supabase.table('topic_clusters').insert(rows[i:i+50]).execute()
            except Exception as e:
                print(f"Failed saving topic clusters: {e}")

        except Exception as e:
            print(f"Monitor extract_and_save_topics error: {e}")


monitor_service = MonitorService()

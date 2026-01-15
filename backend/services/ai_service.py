try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        # Fallback if model not downloaded
        nlp = None
        print("Warning: Spacy model 'en_core_web_sm' not found. Run 'python -m spacy download en_core_web_sm'")
except ImportError:
    nlp = None
    print("Warning: Spacy not installed.")

    print("Warning: Spacy not installed.")

import hashlib
import json
import httpx
import asyncio
import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

HF_API_URL = "https://api-inference.huggingface.co/models/distilbert-base-uncased-finetuned-sst-2-english"

class AIService:
    def __init__(self):
        self.api_url = HF_API_URL

    async def generate_executive_summary(self, reviews: List[str], product_name: str) -> str:
        """
        Generate a business executive summary using LLM.
        """
        if not reviews:
            return "Insufficient data to generate summary."
            
        # Prepare context (Text Blob)
        # Limit to 10-15 short reviews to fit in context
        joined_reviews = "\n- ".join([r[:200] for r in reviews[:15]])
        prompt = f"Summarize these reviews for {product_name} into 3 short, actionable takeaways for the product manager:\n\n{joined_reviews}\n\nSummary:"
        
        API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"
        
        token = await self._get_api_key()
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await self._query_hf(client, API_URL, {
                    "inputs": prompt, 
                    "parameters": {"max_length": 150, "temperature": 0.7}
                }, headers)
                
                if isinstance(response, dict) and "error" in response:
                    return "AI Summary unavailable (Model loading or API limit)."
                    
                if isinstance(response, list) and len(response) > 0:
                    return response[0].get("generated_text", "No summary generated.")
                    
                return "Analysis complete, but summary generation failed."
            except Exception as e:
                print(f"Summary Gen Error: {e}")
                return "AI Summary service currently unavailable."

    async def _get_api_key(self) -> str:
        try:
            from database import supabase
            response = supabase.table("integrations").select("api_key").eq("platform", "huggingface").eq("active", True).limit(1).execute()
            if response.data:
                return response.data[0]["api_key"]
            return os.environ.get("HF_TOKEN", "")
        except:
            return os.environ.get("HF_TOKEN", "")
            
    def _compute_hash(self, text: str) -> str:
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    async def _check_cache(self, text_hash: str) -> Dict[str, Any]:
        """Check if we have analyzed this exact text before."""
        try:
            from database import supabase
            # Check sentiment_analysis table directly? No, we need to find review with this hash?
            # Or assume we store hash? We don't store hash.
            # We must search reviews by text? Too slow.
            # The prompt suggested "Database Caching". 
            # Ideally we'd modify schema to add hash, but for now let's skip complex schema changes 
            # and just try to find exact match if length is reasonable.
            # Actually, to follow the instruction strictly "Check Supabase... WHERE review_text_hash = ...",
            # implies we CAN check by Hash. Since we didn't add the column yet, let's just 
            # check based on exact text match on 'reviews' table first, then get the analysis.
            # But 'reviews' table might not have it yet if this is a new request.
            # So this is really about caching *generic* inputs.
            # Let's verify if 'sentiment_analysis' has a 'text_hash' column? No.
            # We will proceed without caching for now OR add the column.
            # Wait, the instruction said "Implement Hashing... in database.py". 
            # I'll implement the logic here but return None effectively until schema is updated,
            # OR I will just skip caching for this specific file edit and do it in database.py as requested.
            pass
        except:
            pass
        return None

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment, emotions, and credibility of a text string.
        """
        if not text or not text.strip():
            return {"label": "NEUTRAL", "score": 0.5, "emotions": [], "credibility": 0, "credibility_reasons": []}

        # 1. Check Cache
        try:
            from database import get_analysis_by_hash
            text_hash = self._compute_hash(text)
            cached = await get_analysis_by_hash(text_hash)
            if cached:
                print(f"✓ Using cached analysis for hash {text_hash[:8]}")
                return {
                    "label": cached.get("label"),
                    "score": float(cached.get("score") or 0.0),
                    "emotions": cached.get("emotions", []),
                    "credibility": float(cached.get("credibility") or 0.0),
                    "credibility_reasons": cached.get("credibility_reasons", []),
                    "aspects": cached.get("aspects", [])
                }
        except Exception as e:
             print(f"Cache check failed: {e}")

        token = await self._get_api_key()
        headers = {"Authorization": f"Bearer {token}"} if token else {}

        if not token:
             # STRICT MODE: No mocks allowed.
             # Try the key provided by user in chat if not in env
             # STRICT MODE: No mocks allowed.
             # Token must be in .env
             pass 
             
        if not token:
             raise Exception("Real-Time Mode Error: HF_TOKEN is missing. Cannot perform sentiment analysis.")

        async with httpx.AsyncClient() as client:
            try:
                # 1. Sentiment Analysis (Positive/Neutral/Negative)
                sentiment_task = self._query_hf(client, self.api_url, {"inputs": text[:512]}, headers)
                
                # 2. Emotion Analysis (Joy, Anger, etc.)
                EMOTION_API_URL = "https://api-inference.huggingface.co/models/j-hartmann/emotion-english-distilroberta-base"
                emotion_task = self._query_hf(client, EMOTION_API_URL, {"inputs": text[:512]}, headers)
                
                results = await asyncio.gather(sentiment_task, emotion_task, return_exceptions=True)
                
                sentiment_data = results[0]
                emotion_data = results[1]

                if isinstance(sentiment_data, Exception): raise sentiment_data
                if isinstance(emotion_data, Exception): raise emotion_data
                
                # Process Sentiment
                sentiment_res = self._process_sentiment(sentiment_data)
                
                # Process Emotions
                emotions = self._process_emotions(emotion_data)
                
                # Calculate Credibility (Heuristic is still code-based but acceptable as feature)
                cred_result = self._calculate_credibility(text)
                credibility = cred_result["score"]
                cred_reasons = cred_result["reasons"]

                return {
                    "label": sentiment_res["label"],
                    "score": sentiment_res["score"],
                    "breakdown": sentiment_res["breakdown"],
                    "emotions": emotions,
                    "credibility": credibility,
                    "credibility_reasons": cred_reasons,
                    "aspects": self._extract_aspects(text, sentiment_res["label"])
                }

            except Exception as e:
                print(f"AI Service Exception: {e}")
                return {"label": "NEUTRAL", "score": 0.5, "error": str(e)}

    async def _query_hf(self, client, url, payload, headers):
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            # Propagate error details
            try:
                err_json = response.json()
                error_msg = err_json.get("error", f"HTTP {response.status_code}")
                # Handling model loading specifically
                if "estimated_time" in err_json:
                    error_msg = f"Model Loading ({err_json['estimated_time']}s)"
                print(f"HF Error {url}: {error_msg}")
                return {"error": error_msg}
            except:
                print(f"HF Error {url}: {response.text}")
                return {"error": f"HTTP {response.status_code}"}
        return response.json()

    def _process_sentiment(self, data) -> Dict[str, Any]:
        try:
            # Check for API Error first
            if isinstance(data, dict) and "error" in data:
                return {"label": "ERROR", "score": 0.0, "breakdown": [], "error": data["error"]}

            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                scores = data[0]
                top_result = max(scores, key=lambda x: x['score'])
                return {
                    "label": top_result['label'].upper(),
                    "score": top_result['score'],
                    "breakdown": scores
                }
            return {"label": "NEUTRAL", "score": 0.5, "breakdown": []}
        except Exception as e:
            print(f"Sentiment Process Error: {e}")
            return {"label": "NEUTRAL", "score": 0.5, "breakdown": []}

    def _process_emotions(self, data) -> List[Dict[str, Any]]:
        # Expected format: [[{'label': 'joy', 'score': 0.9}, ...]]
        try:
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                # Sort by score desc
                sorted_emotions = sorted(data[0], key=lambda x: x['score'], reverse=True)
                return [{"name": e['label'].title(), "score": e['score'] * 100} for e in sorted_emotions]
            return []
        except:
            return []

    def _calculate_credibility(self, text: str) -> Dict[str, Any]:
        """
        Heuristic credibility score (0-100) with reasons.
        Includes checks for spam, bots, and quality.
        """
        score = 100 # Start perfect
        reasons = []
        text_lower = text.lower()
        
        # 1. Content Length
        if len(text) < 15: 
            score -= 30
            reasons.append("Very short content")
        elif len(text) > 500: 
            # Very long reviews are usually credible, but check for copy-paste loops
            pass
        
        # 2. Capitalization Shouting
        caps_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0
        if caps_ratio > 0.6: 
            score -= 40
            reasons.append("Excessive capitalization")
        
        # 3. Spam keywords
        spam_words = ["buy now", "click here", "subscribe", "winner", "crypto", "nft", "100% free", "call now"]
        if any(w in text_lower for w in spam_words): 
            score -= 50
            reasons.append("Spam keywords detected")
            
        # 4. AI Patterns
        ai_words = ["as an ai", "start with", "generate a review", "prompts"]
        if any(w in text_lower for w in ai_words):
             score -= 80
             reasons.append("AI generation artifacts")

        # 5. Repeated Content (e.g. "Good Good Good")
        words = text_lower.split()
        if len(words) > 5:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.4:
                score -= 30
                reasons.append("Repetitive wording")

        # 6. URL density
        if "http" in text_lower:
            url_count = text_lower.count("http")
            if url_count > 1 and len(words) < 30:
                score -= 40
                reasons.append("Link farm")
            
        return {"score": max(min(score, 100), 0), "reasons": reasons}

    def _extract_aspects(self, text: str, global_sentiment: str) -> List[Dict[str, Any]]:
        """
        Extract aspects using Spacy dependency parsing if available, else fallback to keywords.
        """
        if not nlp:
             # Fallback to keywords if Spacy not loaded
            text_lower = text.lower()
            aspects = []
            keywords = {
                "Quality": ["quality", "build", "material", "durable", "broke", "solid"],
                "Price": ["price", "cost", "value", "expensive", "cheap", "worth"],
                "Shipping": ["shipping", "delivery", "arrived", "package", "packaging"],
                "Service": ["service", "support", "refund", "response", "staff"]
            }
            for category, terms in keywords.items():
                if any(term in text_lower for term in terms):
                    aspects.append({
                        "name": category,
                        "sentiment": global_sentiment.lower() if global_sentiment else "neutral"
                    })
            return aspects

        # Spacy Logic
        doc = nlp(text)
        aspects = {}
        
        # Iterate through tokens to find Nouns described by Adjectives
        for token in doc:
            if token.pos_ in ["NOUN", "PROPN"]:
                # Check for adjectival modifiers (amod) or subject/object relationships
                sentiment_descriptor = None
                
                # Case 1: "Expensive price" (amod)
                for child in token.children:
                    if child.dep_ == "amod" and child.pos_ == "ADJ":
                        sentiment_descriptor = child.text
                        break
                
                # Case 2: "Price is high" (acomp via attr/cop) - simplified to looking at head
                if not sentiment_descriptor and token.dep_ == "nsubj":
                    if token.head.pos_ == "ADJ": # "Price is good"
                        sentiment_descriptor = token.head.text
                    elif token.head.pos_ == "VERB": # "Shipping took long"
                         for child in token.head.children:
                             if child.dep_ == "acomp" and child.pos_ == "ADJ":
                                 sentiment_descriptor = child.text
                
                if sentiment_descriptor:
                    # Simple Sentiment Analysis of the descriptor
                    # In a real app, we'd run another mini-inference or use a lexicon.
                    # Here we use a mini-lexicon for speed
                    desc_lower = sentiment_descriptor.lower()
                    local_sentiment = "neutral"
                    
                    pos_words = ["good", "great", "amazing", "fast", "solid", "excellent", "worth", "best", "love", "nice"]
                    neg_words = ["bad", "terrible", "slow", "expensive", "poor", "worst", "broke", "hard", "disappointed", "waste"]
                    
                    if any(w in desc_lower for w in pos_words): local_sentiment = "positive"
                    elif any(w in desc_lower for w in neg_words): local_sentiment = "negative"
                    
                    aspect_name = token.text.title()
                    # Filter for relevant aspects only (optional, but cleaner)
                    relevant_topics = ["Quality", "Price", "Shipping", "Service", "Battery", "Design", "Screen", "Sound"]
                    # Simple mapping
                    for topic in relevant_topics:
                        if topic.lower() in aspect_name.lower():
                            aspect_name = topic
                            break
                            
                    aspects[aspect_name] = local_sentiment

        return [{"name": k, "sentiment": v} for k, v in aspects.items()]

    def extract_keywords(self, texts: List[str], top_n: int = 50) -> List[Dict[str, Any]]:
        """
        Extract frequent keywords/topics from a list of texts using Scikit-Learn.
        Removes stopwords and extracts top N meaningful terms (unigrams/bigrams).
        """
        if not texts:
            return []

        try:
            from sklearn.feature_extraction.text import CountVectorizer
            
            # Custom stop words + standar English list
            stop_words = 'english'
            
            # Use CountVectorizer to extract top words
            # ngram_range=(1, 2) lets us capture "battery life" or "screen"
            vectorizer = CountVectorizer(stop_words=stop_words, max_features=top_n, ngram_range=(1, 2))
            X = vectorizer.fit_transform(texts)
            
            # Sum word counts
            word_counts = X.toarray().sum(axis=0)
            words = vectorizer.get_feature_names_out()
            
            # Zip and sort
            freqs = sorted(zip(words, word_counts), key=lambda x: x[1], reverse=True)
            
            return [{"text": word, "value": int(count)} for word, count in freqs[:top_n]]
            
        except ImportError:
            # Fallback if scikit-learn is missing
            print("Warning: scikit-learn not found, using simple fallback.")
            from collections import Counter
            import re
            all_text = " ".join(texts).lower()
            words = re.findall(r'\w+', all_text)
            common = Counter(words).most_common(top_n)
            return [{"text": w, "value": c} for w, c in common]
        except Exception as e:
            print(f"Keyword Extraction Error: {e}")
            return []

    async def generate_topic_clusters(self, reviews: List[str], top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Generate topic clusters from a list of reviews.
        - Extract most common nouns (using Spacy if available, else fallback to word frequency)
        - For each topic, compute average sentiment score from reviews that mention the topic
        - Persist a row to `topic_analysis` for each topic
        Returns a list of topic dicts: {topic_name, sentiment, size, keywords}
        """
        if not reviews:
            return []

        from collections import Counter
        import re
        try:
            from database import supabase
        except Exception:
            supabase = None

        # 1) Extract candidate topic tokens
        candidate_tokens = []
        if nlp:
            for r in reviews:
                try:
                    doc = nlp(r)
                    for token in doc:
                        if token.pos_ in ("NOUN", "PROPN") and len(token.text) > 2 and not token.is_stop:
                            candidate_tokens.append(token.lemma_.lower())
                except Exception:
                    continue
        else:
            # Fallback: use extract_keywords which already removes stopwords
            kw = self.extract_keywords(reviews, top_n=200)
            candidate_tokens = [k["text"] for k in kw]

        if not candidate_tokens:
            return []

        counts = Counter(candidate_tokens)
        top_topics = [t for t, _ in counts.most_common(top_n)]

        topics_output = []

        # Normalize reviews for matching
        normalized_reviews = [r.lower() for r in reviews]

        # We'll reuse analyze_sentiment to compute a numeric score (0-1)
        for topic in top_topics:
            # Find reviews mentioning the topic token (simple substring match)
            related_indices = [i for i, r in enumerate(normalized_reviews) if re.search(r"\b" + re.escape(topic) + r"\b", r)]
            if not related_indices:
                continue

            # Compute sentiment scores for related reviews
            sentiment_scores = []
            for idx in related_indices:
                try:
                    sentiment = await self.analyze_sentiment(reviews[idx])
                    score = float(sentiment.get("score") or 0.0)
                    sentiment_scores.append(score)
                except Exception:
                    continue

            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0

            # Extract keywords from related reviews (top 5)
            related_texts = [reviews[i] for i in related_indices]
            keywords_objs = self.extract_keywords(related_texts, top_n=10)
            keywords = [k["text"] for k in keywords_objs[:5]]

            topic_entry = {
                "topic_name": topic,
                "sentiment": avg_sentiment,
                "size": len(related_indices),
                "keywords": keywords,
            }

            # Persist to DB if supabase available
            if supabase:
                try:
                    supabase.table("topic_analysis").insert({
                        "topic_name": topic,
                        "sentiment": avg_sentiment,
                        "size": len(related_indices),
                        "keywords": keywords,
                    }).execute()
                except Exception as e:
                    print(f"Failed saving topic_analysis for {topic}: {e}")

            topics_output.append(topic_entry)

        return topics_output

    async def check_for_alerts(self, review: Dict[str, Any]):
        """
        Create an alert in the `alerts` table if sentiment score below threshold.
        Expects review dict that may contain 'score' or 'sentiment_score'.
        """
        try:
            from database import supabase
        except Exception:
            supabase = None

        # Extract score
        score = None
        if isinstance(review, dict):
            score = review.get("score") or review.get("sentiment_score")
            # If nested under 'analysis'
            if score is None and review.get("analysis"):
                score = review["analysis"].get("score")

        try:
            score = float(score) if score is not None else None
        except Exception:
            score = None

        if score is None:
            # Try to compute sentiment on review text if present
            text = review.get("text") or review.get("review_text") if isinstance(review, dict) else None
            if text:
                try:
                    analysis = await self.analyze_sentiment(text)
                    score = float(analysis.get("score") or 0.0)
                except Exception:
                    score = None

        if score is None:
            return None

        # Trigger alert when sentiment < 0.3
        if score < 0.3:
            alert_payload = {
                "type": "sentiment_drop",
                "severity": "high" if score < 0.15 else "medium",
                "title": "Negative sentiment detected",
                "message": review.get("text") or review.get("review_text") or "",
                "platform": review.get("platform") if isinstance(review, dict) else None,
                "is_read": False
            }
            if supabase:
                try:
                    supabase.table("alerts").insert(alert_payload).execute()
                except Exception as e:
                    print(f"Failed to insert alert: {e}")
            return alert_payload

        return None

ai_service = AIService()

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

import hashlib
import json

class AIService:
    def __init__(self):
        self.api_url = HF_API_URL

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
             # Fallback to simple logic if no key provided
             print("Warning: No HF Token found. Using mock fallback.")
             # Simple heuristic for fallback
             sentiment = "POSITIVE" if "good" in text.lower() or "love" in text.lower() else "NEGATIVE" if "bad" in text.lower() else "NEUTRAL"
             return {
                "label": sentiment, 
                "score": 0.6, 
                "emotions": [{"name": "Neutral", "score": 70}], 
                "credibility": 50,
                "credibility_reasons": ["Fallback Mode"],
                "aspects": self._extract_aspects(text, sentiment)
             }


        async with httpx.AsyncClient() as client:
            try:
                # 1. Sentiment Analysis (Positive/Neutral/Negative)
                sentiment_task = self._query_hf(client, self.api_url, {"inputs": text[:512]}, headers)
                
                # 2. Emotion Analysis (Joy, Anger, etc.)
                EMOTION_API_URL = "https://api-inference.huggingface.co/models/j-hartmann/emotion-english-distilroberta-base"
                emotion_task = self._query_hf(client, EMOTION_API_URL, {"inputs": text[:512]}, headers)
                
                results = await asyncio.gather(sentiment_task, emotion_task, return_exceptions=True)
                
                sentiment_data = results[0] if not isinstance(results[0], Exception) else []
                emotion_data = results[1] if not isinstance(results[1], Exception) else []
                
                # Process Sentiment
                sentiment_res = self._process_sentiment(sentiment_data)
                
                # Process Emotions
                emotions = self._process_emotions(emotion_data)
                
                # Calculate Credibility (Heuristic)
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
        """
        score = 80 # Start high
        reasons = []
        
        # 1. Content Length
        if len(text) < 20: 
            score -= 20
            reasons.append("Very short content")
        elif len(text) > 100: 
            score += 10
            reasons.append("Detailed review")
        
        # 2. Capitalization Shouting
        caps_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0
        if caps_ratio > 0.5: 
            score -= 30
            reasons.append("Excessive capitalization")
        
        # 3. Spam keywords
        spam_words = ["buy now", "click here", "subscribe", "winner", "crypto"]
        if any(w in text.lower() for w in spam_words): 
            score -= 40
            reasons.append("Spam keywords detected")
            
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
        Extract frequent keywords/topics from a list of texts.
        Basic implementation: Tokenization + Stopword Removal + Frequency.
        """
        from collections import Counter
        import re

        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
            "is", "was", "are", "were", "be", "been", "this", "that", "these", "those",
            "it", "i", "you", "he", "she", "we", "they", "my", "your", "his", "her", "their",
            "what", "which", "who", "whom", "whose", "why", "how", "where", "when",
            "from", "as", "by", "about", "into", "through", "during", "before", "after",
            "above", "below", "up", "down", "out", "off", "over", "under", "again", "further",
            "then", "once", "here", "there", "all", "any", "both", "each", "few", "more",
            "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same",
            "so", "than", "too", "very", "can", "will", "just", "don", "should", "now"
        }

        all_words = []
        for text in texts:
            # Simple normalization
            clean_text = re.sub(r'[^\w\s]', '', text.lower())
            words = clean_text.split()
            filtered = [w for w in words if w not in stopwords and len(w) > 2]
            all_words.extend(filtered)

        counter = Counter(all_words)
        most_common = counter.most_common(top_n)

        # Format for Word Cloud (text, value)
        return [{"text": word, "value": count} for word, count in most_common]

ai_service = AIService()

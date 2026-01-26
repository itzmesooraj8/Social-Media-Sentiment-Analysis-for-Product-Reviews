import re
import asyncio
from functools import lru_cache
from typing import Dict, List, Any
import logging

# --- Imports with Safety Checks ---
try:
    from transformers import pipeline
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    _TRANSFORMERS_AVAILABLE = False
    print("⚠️ Transformers not found. AI features will be limited.")

try:
    import textstat
    _TEXTSTAT_AVAILABLE = True
except ImportError:
    _TEXTSTAT_AVAILABLE = False
    print("⚠️ textstat not found. Credibility scoring will be limited.")

try:
    from keybert import KeyBERT
    _KEYBERT_AVAILABLE = True
except ImportError:
    _KEYBERT_AVAILABLE = False
    print("⚠️ KeyBERT not found. Advanced keyphrase extraction will be limited.")

try:
    from sklearn.feature_extraction.text import CountVectorizer
    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False
    print("⚠️ sklearn not found. Topic extraction will be limited.")

try:
    from nrclex import NRCLex
    import nltk
    # Ensure necessary NLTK data is available for NRCLex
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    _NRC_AVAILABLE = True
except ImportError:
    _NRC_AVAILABLE = False
    print("⚠️ NRCLex/NLTK not found. Advanced emotion detection will be limited.")

try:
    import gensim
    from gensim import corpora
    _GENSIM_AVAILABLE = True
except ImportError:
    _GENSIM_AVAILABLE = False
    print("⚠️ Gensim not found. LDA Topic modeling will be limited.")

# ----------------------------------

from database import supabase

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        # Using a fine-tuned BERT model (DistilBERT) for sentiment as it's faster and effective
        self.sentiment_model = "distilbert-base-uncased-finetuned-sst-2-english"
        self.emotion_model = "j-hartmann/emotion-english-distilroberta-base"
        self._sentiment_pipe = None
        self._emotion_pipe = None
        self._keybert_model = None
        self._models_loaded = False

    def _ensure_models_loaded(self):
        if self._models_loaded or not _TRANSFORMERS_AVAILABLE:
            return

        try:
            print("[Loading] Sentiment Model (Lazy Load)...")
            self._sentiment_pipe = pipeline("sentiment-analysis", model=self.sentiment_model)
            print("[Loading] Emotion Model (Lazy Load)...")
            self._emotion_pipe = pipeline("text-classification", model=self.emotion_model, top_k=1)
            
            if _KEYBERT_AVAILABLE:
                 print("[Loading] KeyBERT Model (Lazy Load)...")
                 self._keybert_model = KeyBERT()

            print("[OK] AI Models Loaded.")
            self._models_loaded = True
        except Exception as e:
            print(f"[ERROR] AI Init Error: {e}")
            self._models_loaded = True # Prevent retry loop on failure

    def _normalize_label(self, raw_label: str) -> str:
        lbl = (raw_label or "").upper()
        if lbl in ("POSITIVE", "NEGATIVE"):
            return lbl
        if lbl.endswith("_0"):
            return "NEGATIVE"
        if lbl.endswith("_1"):
            return "POSITIVE"
        return "NEUTRAL"

    def _compute_credibility(self, text: str, confidence: float, metadata: Dict[str, Any] = None) -> float:
        """
        Multi-Factor Credibility Score:
        Formula = (0.4 * Sentiment_Confidence) + (0.3 * Readability_Score) + (0.3 * Metadata_Impact)
        """
        if not text or not text.strip():
            return 0.1

        # 1. Sentiment Confidence (0.4 weight) - passed in from model
        conf_score = confidence if confidence else 0.5
        
        # 2. Readability Score (0.3 weight)
        readability_val = 0.5
        if _TEXTSTAT_AVAILABLE:
            try:
                # Flesch Reading Ease: 0-100 (higher is easier). We normalize to 0-1.
                ease = textstat.flesch_reading_ease(text)
                readability_val = max(0.0, min(1.0, ease / 100.0))
            except Exception:
                readability_val = 0.5
        
        # 3. Metadata Impact (0.3 weight)
        meta_val = 0.0
        if metadata:
            # Normalize likes/replies/retweets. 
            likes = metadata.get("like_count", 0)
            replies = metadata.get("reply_count", 0)
            retweets = metadata.get("retweet_count", 0)
            total_engagement = likes + replies + retweets
            
            if total_engagement > 100: meta_val = 1.0
            elif total_engagement > 10: meta_val = 0.7
            elif total_engagement > 0: meta_val = 0.4
            else: meta_val = 0.1 
        else:
             meta_val = 0.3 

        final_score = (0.4 * conf_score) + (0.3 * readability_val) + (0.3 * meta_val)
        return round(final_score, 3)

    @lru_cache(maxsize=1000)
    def _predict_sentiment_cached(self, text: str):
        """Cached model inference."""
        self._ensure_models_loaded()
        
        # Default values
        label = "NEUTRAL"
        score = 0.5
        emotion = "neutral"
        final_emotion_score = 0.5
        
        # 1. Sentiment Analysis (Transformers)
        if self._sentiment_pipe:
            try:
                out = self._sentiment_pipe(text[:512])
                if out and isinstance(out, list):
                    top = out[0]
                    label = self._normalize_label(top.get("label"))
                    score = float(top.get("score", 0.5))
            except Exception as e:
                print(f"Sentiment error: {e}")

        # 2. Emotion Logic (Transformers fallback + Custom)
        if label == "POSITIVE" and score > 0.8:
            emotion = "Joy/Excitement"
            final_emotion_score = score
        elif label == "NEGATIVE" and score > 0.8: 
            emotion = "Anger/Disappointment"
            final_emotion_score = score
        else:
            emotion = "Neutral/Curiosity"
            final_emotion_score = 0.5
        
        # If we have a specific emotion model loaded, use it for better granularity
        if self._emotion_pipe:
            try:
                e_out = self._emotion_pipe(text[:512])
                if e_out and isinstance(e_out, list):
                    top_e = e_out[0]
                    emotion = top_e.get("label")
                    final_emotion_score = float(top_e.get("score", 0.5))
            except Exception as e:
                pass # Fallback to logic above

        return label, score, emotion, final_emotion_score

    def _analyze_emotions_nrc(self, text: str) -> List[Dict[str, Any]]:
        """
        Analyze emotions using NRCLex (Lexicon-based).
        Good for detecting: fear, anger, anticipation, trust, surprise, positive, negative, sadness, disgust, joy.
        """
        if not _NRC_AVAILABLE:
            return []
        
        try:
            emotion_obj = NRCLex(text)
            # raw_emotion_scores is a dict like {'fear': 0.1, 'joy': 0.5}
            scores = emotion_obj.raw_emotion_scores
            # Normalize to list of dicts
            total = sum(scores.values()) if scores else 1
            results = []
            for emo, val in scores.items():
                results.append({"name": emo, "score": int((val / total) * 100)})
            
            # Sort by score desc
            results.sort(key=lambda x: x["score"], reverse=True)
            return results
        except Exception as e:
            print(f"NRCLex error: {e}")
            return []

    def analyze_text(self, text: str, metadata: Dict[str, Any] = None) -> Dict[str, any]:
        """Synchronous analyze with Real Emotion & Aspect Detection."""
        if not text or not text.strip():
            return {"label": "NEUTRAL", "score": 0.5, "emotion": "neutral", "credibility": 0.1, "aspects": []}

        # Call cached inference
        label, score, emotion, final_emotion_score = self._predict_sentiment_cached(text)
        
        # Get advanced emotions if available
        nrc_emotions = self._analyze_emotions_nrc(text)
        
        # Combine primary emotion with NRC results if needed, or just use NRC as details
        # For now, we return the primary model emotion as the main one, and nrc as details if we extended the schema
        # But the current return schema expects a list for 'emotions'. 
        
        emotions_list = [{"name": emotion, "score": int(final_emotion_score * 100)}]
        if nrc_emotions:
            # Merge or append? Let's append unique ones or keep top NRC
            for nrc_e in nrc_emotions[:3]: # Top 3 NRC
                if nrc_e["name"].lower() != emotion.lower():
                     emotions_list.append(nrc_e)

        # 3. Aspect Logic
        text_lower = text.lower()
        aspects_found = []
        
        keywords = {
            "price": ["cost", "expensive", "cheap", "value", "$"],
            "quality": ["build", "break", "material", "feel"],
            "shipping": ["delivery", "arrive", "late", "fast"],
            "service": ["support", "refund", "rude", "helpful"]
        }
        
        for aspect_name, triggers in keywords.items():
            for trigger in triggers:
                if trigger in text_lower:
                    aspect_sentiment = "neutral"
                    if label == "POSITIVE": aspect_sentiment = "positive"
                    elif label == "NEGATIVE": aspect_sentiment = "negative"
                    
                    aspects_found.append({
                        "aspect": aspect_name,
                        "sentiment": aspect_sentiment,
                        "score": score
                    })
                    break 

        credibility = self._compute_credibility(text, score, metadata)

        # 4. Topic/Keyword Extraction (Simple per-text)
        topics = []
        if _SKLEARN_AVAILABLE:
             try:
                 vectorizer = CountVectorizer(ngram_range=(2, 2), stop_words='english', max_features=5)
                 vectorizer.fit_transform([text])
                 topics = vectorizer.get_feature_names_out().tolist()
             except Exception:
                 pass
        
        if not topics and len(text.split()) > 4:
             words = re.sub(r'[^\w\s]', '', text.lower()).split()
             topics = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1) if len(words[i]) > 3 and len(words[i+1]) > 3][:5]

        return {
            "label": label,
            "score": round(score, 4),
            "emotions": emotions_list,
            "aspects": aspects_found,
            "credibility": credibility,
            "topics": topics
        }
    
    async def analyze_sentiment(self, text: str, metadata: Dict[str, Any] = None):
        """Async wrapper."""
        return await asyncio.to_thread(self.analyze_text, text, metadata)

    def extract_topics_lda(self, texts: List[str], num_topics: int = 5, num_words: int = 4) -> List[Dict[str, Any]]:
        """
        Extract topics using LDA (Delegates to NLPService).
        """
        from services.nlp_service import nlp_service
        return nlp_service.extract_topics_lda(texts, num_topics, num_words)

    def extract_topics_simple(self, texts: List[str], top_k: int = 5) -> List[Dict[str, any]]:
        """
        Extract topics using Bigram Frequency (Fallback / Simple).
        """
        if not texts:
            return []

        # 1. Normalize
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "is", "was", "are", "were", "it", "this", "that", "i", "my", "we", "our", "you", "your", "good", "bad", "great", "product", "review", "phone", "app", "very", "so", "really", "video", "just", "like", "have", "has", "had", "not", "dont", "cant", "wont"}
        
        normalized_texts = []
        for t in texts:
            # Lowercase, remove punctuation (basic), split
            cleaned = re.sub(r'[^\w\s]', '', t.lower())
            words = [w for w in cleaned.split() if w not in stop_words and len(w) > 2]
            normalized_texts.append(words)

        # 2. Create Bigrams & Count
        bigram_counts = {}
        
        for words in normalized_texts:
            if len(words) < 2:
                continue
            for i in range(len(words) - 1):
                bigram = f"{words[i]} {words[i+1]}"
                bigram_counts[bigram] = bigram_counts.get(bigram, 0) + 1

        # 3. Sort and Return Top K
        sorted_bigrams = sorted(bigram_counts.items(), key=lambda x: x[1], reverse=True)
        top_bigrams = sorted_bigrams[:top_k]
        
        results = []
        for bg, count in top_bigrams:
            results.append({
                "topic": bg,
                "sentiment": "neutral", 
                "count": count
            })
            
        return results

    # Alias for backward compatibility if needed, or just cleaner naming
    extract_topics = extract_topics_simple

    async def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Batch analysis for high volume.
        Currently simple loop, but prepared for pipeline batching if memory allows.
        """
        self._ensure_models_loaded()
        
        results = []
        # If we had a GPU, we would pass list to pipe(). 
        # On CPU, sometimes list is faster too, but let's be safe with memory.
        # Transformers pipeline can take a list/generator.
        
        # Check if we can use pipeline batching
        if self._sentiment_pipe:
            try:
                # Process in chunks of 32
                chunk_size = 32
                for i in range(0, len(texts), chunk_size):
                    batch = texts[i:i+chunk_size]
                    # This returns a list of dicts for the batch
                    # Only safe if texts are not too long and memory is okay.
                    # Fallback to loop if unsure. 
                    # For now, let's use the robust analyze_text loop to ensure all features (credibility, aspects) are present
                    # Pipeline batching ONLY gives sentiment. We need aspects/credibility/etc.
                    pass
            except Exception:
                pass

        # Use asyncio.gather for concurrency if doing I/O, but here it's CPU bound.
        # Running in thread pool is best to not block event loop.
        
        loop = asyncio.get_running_loop()
        tasks = [loop.run_in_executor(None, self.analyze_text, text) for text in texts]
        results = await asyncio.gather(*tasks)
        
        return results

ai_service = AIService()
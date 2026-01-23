import re
from collections import Counter
from functools import lru_cache
from typing import Dict, List
import os
import asyncio

try:
    from transformers import pipeline
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    _TRANSFORMERS_AVAILABLE = False
    print("⚠️ Transformers not found. AI features will be limited.")

from database import supabase


class AIService:
    def __init__(self):
        self.sentiment_model = "distilbert-base-uncased-finetuned-sst-2-english"
        self.emotion_model = "j-hartmann/emotion-english-distilroberta-base"
        self._sentiment_pipe = None
        self._emotion_pipe = None

        if _TRANSFORMERS_AVAILABLE:
            try:
                print("[Loading] Sentiment Model...")
                self._sentiment_pipe = pipeline("sentiment-analysis", model=self.sentiment_model)
                print("[Loading] Emotion Model...")
                self._emotion_pipe = pipeline("text-classification", model=self.emotion_model, top_k=1)
                print("[OK] AI Models Loaded.")
            except Exception as e:
                print(f"[ERROR] AI Init Error: {e}")

    def _normalize_label(self, raw_label: str) -> str:
        lbl = (raw_label or "").upper()
        if lbl in ("POSITIVE", "NEGATIVE"):
            return lbl
        if lbl.endswith("_0"):
            return "NEGATIVE"
        if lbl.endswith("_1"):
            return "POSITIVE"
        return "NEUTRAL"

    def _compute_credibility(self, text: str) -> float:
        """Simple credibility heuristic."""
        try:
            length = len(text.strip())
            if length < 10:
                base = 0.15
            elif length < 50:
                base = 0.45
            else:
                base = 0.75

            # Duplicate check (simple cache check could go here, but DB check is expensive in loop)
            # For high-performance, we skip the DB check in this synchronous part or use a local bloom filter.
            # We will stick to length-based for now to ensure speed.
            return float(min(1.0, max(0.0, base)))
        except Exception:
            return 0.5

    @lru_cache(maxsize=2048)
    def analyze_text(self, text: str) -> Dict[str, any]:
        """Synchronous analyze. Cached to avoid repeated work."""
        if not text or not text.strip():
            return {"label": "NEUTRAL", "score": 0.5, "emotion": "neutral", "credibility": 0.1}

        label = "NEUTRAL"
        score = 0.5
        emotion = "neutral"

        # 1. Sentiment Analysis
        if self._sentiment_pipe:
            try:
                out = self._sentiment_pipe(text[:512])
                if out and isinstance(out, list):
                    top = out[0]
                    label = self._normalize_label(top.get("label"))
                    score = float(top.get("score", 0.5))
            except Exception as e:
                print(f"Sentiment error: {e}")

        # 2. Emotion Analysis (Real Model)
        if self._emotion_pipe:
            try:
                e_out = self._emotion_pipe(text[:512])
                # e_out structure with top_k=1: [{'label': 'joy', 'score': 0.9}]
                if e_out and isinstance(e_out, list):
                    if isinstance(e_out[0], list): # Handle batch output edge case
                        top_e = e_out[0][0]
                    else:
                        top_e = e_out[0]
                    
                    emotion = top_e.get("label", "neutral")
            except Exception as e:
                print(f"Emotion error: {e}")
        else:
            # Fallback heuristic if model failed to load
            text_l = text.lower()
            if label == "POSITIVE":
                emotion = "joy"
            elif label == "NEGATIVE":
                emotion = "anger"

        credibility = self._compute_credibility(text)
        
        return {
            "label": label,
            "score": round(score, 4),
            "emotion": emotion,
            "credibility": round(credibility, 3)
        }
    
    async def analyze_sentiment(self, text: str):
        """Async wrapper for the sync lru_cache method"""
        return await asyncio.to_thread(self.analyze_text, text)

    def extract_topics(self, texts: List[str], top_k: int = 5) -> List[Dict[str, any]]:
        """
        Extract top topics using LDA (Latent Dirichlet Allocation) if possible,
        otherwise fall back to frequency analysis.
        """
        if not texts:
            return []
        
        # Simple cleaning for topic extraction specifically
        clean_texts = [re.sub(r'http\S+', '', t).lower() for t in texts if t]
        clean_texts = [re.sub(r'[^\w\s]', '', t) for t in clean_texts if t.strip()]

        # Try LDA if we have enough data (at least 10 documents) and sklearn is available
        if len(clean_texts) >= 10:
            try:
                from sklearn.feature_extraction.text import CountVectorizer
                from sklearn.decomposition import LatentDirichletAllocation
                import numpy as np
                
                # Stop words extended
                stopwords = [
                    "the", "is", "and", "to", "a", "of", "in", "it", "for", "on", "that", "this", "with", "i", "you",
                    "but", "was", "my", "have", "as", "are", "not", "be", "so", "at", "if", "or", "just", "very", "can",
                    "product", "item", "one", "get", "me", "all", "about", "out", "has", "more", "like", "when", "up",
                    "what", "time", "would", "they", "from", "do", "will", "really", "good", "great", "review", "video"
                ]

                # Vectorize
                tf_vectorizer = CountVectorizer(max_df=0.95, min_df=2, stop_words=stopwords)
                tf = tf_vectorizer.fit_transform(clean_texts)
                
                # Fit LDA
                n_topics = min(top_k, 5) # Discover 5 topics internally
                lda = LatentDirichletAllocation(n_components=n_topics, max_iter=5, learning_method='online', learning_offset=50., random_state=0)
                lda.fit(tf)
                
                # Extract top words per topic
                feature_names = tf_vectorizer.get_feature_names_out()
                topics = []
                
                for topic_idx, topic in enumerate(lda.components_):
                    # Get top 3 words for this topic
                    top_indices = topic.argsort()[:-4:-1]
                    top_words = [feature_names[i] for i in top_indices]
                    topic_label = " ".join(top_words)
                    
                    # Estimate "size" or importance based on sum of weights
                    importance = float(topic.sum())
                    
                    topics.append({"text": topic_label, "value": int(importance * 10), "sentiment": "neutral"})
                
                # Sort by importance
                topics.sort(key=lambda x: x["value"], reverse=True)
                return topics[:top_k]

            except ImportError:
                print("⚠️ Scikit-learn not found. Falling back to simple frequency analysis.")
            except Exception as e:
                print(f"LDA Topic Extraction failed: {e}. Falling back to simple frequency analysis.")

        # --- Fallback: Frequency Analysis ---

        stopwords = {
            "the", "is", "and", "to", "a", "of", "in", "it", "for", "on", "that", "this", "with", "i", "you",
            "but", "was", "my", "have", "as", "are", "not", "be", "so", "at", "if", "or", "just", "very", "can",
            "product", "item", "one", "get", "me", "all", "about", "out", "has", "more", "like", "when", "up",
            "what", "time", "would", "they", "from", "do", "will", "really", "good", "great"
        }

        all_bigrams = []

        for text in texts:
            if not text:
                continue
            # Simple tokenization
            words = re.findall(r'\b[a-z]{3,}\b', text.lower())
            # Filter stopwords
            words = [w for w in words if w not in stopwords]
            
            # Create bigrams
            if len(words) >= 2:
                for i in range(len(words) - 1):
                    bigram = f"{words[i]} {words[i+1]}"
                    all_bigrams.append(bigram)

        # Count frequencies
        counter = Counter(all_bigrams)
        common = counter.most_common(top_k)

        # Format for frontend { "text": "battery life", "value": 42 }
        topics = [{"text": phrase, "value": count, "sentiment": "neutral"} for phrase, count in common]
        return topics


ai_service = AIService()


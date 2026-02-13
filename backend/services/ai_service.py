import re
import asyncio
from functools import lru_cache
from typing import Dict, List, Any
import logging


from database import supabase

logger = logging.getLogger(__name__)

# --- Imports (Fail Fast) ---

# --- Imports (Fail Fast) ---
try:
    from transformers import pipeline
except ImportError:
    pipeline = None

try:
    import textstat
except ImportError:
    textstat = None

try:
    from keybert import KeyBERT
except ImportError:
    KeyBERT = None

try:
    from sklearn.feature_extraction.text import CountVectorizer
except ImportError:
    CountVectorizer = None

try:
    from nrclex import NRCLex
except ImportError:
    NRCLex = None

try:
    import nltk
except ImportError:
    nltk = None

try:
    import gensim
    from gensim import corpora
except ImportError:
    gensim = None
    corpora = None

try:
    import spacy
except ImportError:
    spacy = None

try:
    from textblob import TextBlob
except ImportError:
    TextBlob = None

# Constants for availability checks
_TRANSFORMERS_AVAILABLE = pipeline is not None
_TEXTBlob_AVAILABLE = TextBlob is not None
_TEXTSTAT_AVAILABLE = textstat is not None
_KEYBERT_AVAILABLE = KeyBERT is not None
_SKLEARN_AVAILABLE = CountVectorizer is not None
_NRC_AVAILABLE = NRCLex is not None
_GENSIM_AVAILABLE = gensim is not None
# ---------------------------

class AIService:
    def __init__(self):
        # Using a fine-tuned BERT model (DistilBERT) for sentiment as it's faster and effective
        self.sentiment_model = "distilbert-base-uncased-finetuned-sst-2-english"
        self.emotion_model = "j-hartmann/emotion-english-distilroberta-base"
        self._sentiment_pipe = None
        self._emotion_pipe = None
        self._keybert_model = None
        self._spacy_nlp = None
        self._models_loaded = False

    def _ensure_models_loaded(self):
        if self._models_loaded:
            return

        # 0. Ensure NLTK Data (Lazy Download)
        # 0. Ensure NLTK Data
        try:
             nltk.data.find('tokenizers/punkt')
        except LookupError:
             logger.info("Downloading NLTK data...")
             nltk.download('punkt', quiet=True)

        logger.info("Loading AI Models...")
        
        # 1. Transformers (Sentiment & Emotion)
        self._sentiment_pipe = pipeline("sentiment-analysis", model=self.sentiment_model)
        self._emotion_pipe = pipeline("text-classification", model=self.emotion_model, top_k=1)
        
        # 2. KeyBERT
        self._keybert_model = KeyBERT()

        # 3. Spacy (Aspects)
        try:
            self._spacy_nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("Downloading Spacy model 'en_core_web_sm'...")
            from spacy.cli import download
            download("en_core_web_sm")
            self._spacy_nlp = spacy.load("en_core_web_sm")

        logger.info("All AI Models Loaded Successfully.")
        self._models_loaded = True

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
        
        reasons = []
        if conf_score > 0.8: reasons.append("High Model Confidence")
        elif conf_score < 0.6: reasons.append("Low Model Confidence")
        
        if readability_val > 0.7: reasons.append("Clear Writing Style")
        elif readability_val < 0.4: reasons.append("Complex/Unclear Text")
        
        if meta_val > 0.6: reasons.append("High Social Engagement")
        elif meta_val < 0.2: reasons.append("Low/No Social Verification")
        
        return round(final_score, 3), reasons

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
                out = self._sentiment_pipe(text[:256])
                if out and isinstance(out, list):
                    top = out[0]
                    label = self._normalize_label(top.get("label"))
                    score = float(top.get("score", 0.5))
            except Exception as e:
                logger.error(f"Sentiment error: {e}")
        elif _TEXTBlob_AVAILABLE:
            # Fallback: TextBlob
            try:
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity
                score = (polarity + 1) / 2 # Normalize -1..1 to 0..1
                if polarity > 0.1: label = "POSITIVE"
                elif polarity < -0.1: label = "NEGATIVE"
                else: label = "NEUTRAL"
            except Exception:
                pass

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
            logger.error(f"NRCLex error: {e}")
            return []

    def analyze_text(self, text: str, metadata: Dict[str, Any] = None) -> Dict[str, any]:
        """Synchronous analyze with Real Emotion & Aspect Detection."""
        if not text or not text.strip():
            return {"label": "NEUTRAL", "score": 0.5, "emotion": "neutral", "credibility": 0.1, "aspects": [], "topics": []}

        # Safe defaults
        label, score, emotion = "NEUTRAL", 0.5, "neutral"
        final_emotion_score = 0.5
        emotions_list = []
        aspects_found = []
        credibility = 0.5
        topics = []

        # 1. Prediction
        try:
             # Call cached inference
             label, score, emotion, final_emotion_score = self._predict_sentiment_cached(text)
        except Exception as e:
             logger.error(f"Prediction error: {e}")

        # 2. Emotions
        try:
            # Get advanced emotions if available
            nrc_emotions = self._analyze_emotions_nrc(text)
            
            emotions_list = [{"name": str(emotion), "score": int(final_emotion_score * 100)}]
            if nrc_emotions:
                for nrc_e in nrc_emotions[:3]: # Top 3 NRC
                    if nrc_e["name"].lower() != emotion.lower():
                         emotions_list.append(nrc_e)
        except Exception as e:
            logger.error(f"Emotion extraction error: {e}")

        # 3. Aspects (God Tier V2)
        # 3. Aspects (Real Dependency Parsing)
        try:
            if self._spacy_nlp:
                doc = self._spacy_nlp(text)
                # Strategy: Find Adjectives (amod) modifying Nouns...
                # ...AND Nouns as subjects of 'be' with adjective complements (acomp).
                
                for token in doc:
                    if token.pos_ == "NOUN" and not token.is_stop:
                        adjectives = []
                        
                        # 1. Direct Modification (e.g. "great battery")
                        adjectives.extend([child for child in token.children if child.dep_ == "amod" and child.pos_ == "ADJ"])
                        
                        # 2. Predicative Adjectives (e.g. "battery is dead")
                        if token.dep_ == "nsubj" and token.head.lemma_ == "be":
                            adjectives.extend([child for child in token.head.children if child.dep_ == "acomp" and child.pos_ == "ADJ"])
                        
                        if adjectives:
                            aspect_name = token.lemma_.lower()
                            # Use the first adjective for sentiment context
                            adj_token = adjectives[0]
                            
                            # Determine local sentiment from the adjective
                            # This is a heuristic. Ideally use the sentiment score of the sentence + adjective polarity.
                            # For now, we fallback to the global sentence label/score but scoped to this aspect.
                            
                            aspect_sent = "neutral"
                            if label == "POSITIVE": aspect_sent = "positive"
                            elif label == "NEGATIVE": aspect_sent = "negative"

                            # Avoid duplicates
                            if aspect_name not in [a["aspect"] for a in aspects_found]:
                                aspects_found.append({
                                    "aspect": aspect_name,
                                    "sentiment": aspect_sent,
                                    "score": float(score)
                                })
            else:
                 logger.error("Spacy model not loaded for aspect extraction")
        except Exception as e:
             logger.error(f"Aspect extraction error: {e}")

        # 4. Credibility
        credibility_reasons = []
        try:
             credibility, credibility_reasons = self._compute_credibility(text, float(score), metadata)
        except Exception as e:
             logger.error(f"Credibility error: {e}")
             credibility = 0.5
             credibility_reasons = ["Analysis Error"]

        # 5. Topics
        try:
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
        except Exception as e:
             logger.error(f"Topic extraction error: {e}")

        return {
            "label": label,
            "score": round(score, 4),
            "emotions": emotions_list,
            "aspects": aspects_found,
            "aspects": aspects_found,
            "credibility": credibility,
            "credibility_reasons": credibility_reasons,
            "topics": topics
        }
    
    async def analyze_sentiment(self, text: str, metadata: Dict[str, Any] = None):
        """Async wrapper."""
        return await asyncio.to_thread(self.analyze_text, text, metadata)

    async def extract_topics(self, texts: List[str], top_k: int = 10) -> List[Dict[str, any]]:
        """
        Smart Topic Extraction. 
        Tries LDA (God Tier), then KeyBERT, then Simple (Fallback).
        """
        if not texts: return []
        
        # 1. Try LDA via NLP Service
        # 1. Try LDA via NLP Service
        try:
             # Lazy import
             from services.nlp_service import nlp_service
             import inspect
             
             # Run in thread to avoid blocking loop (LDA is CPU intensive)
             # And handle if it returns a coroutine or value
             if asyncio.iscoroutinefunction(nlp_service.extract_topics_lda):
                 lda_results = await nlp_service.extract_topics_lda(texts, num_topics=top_k)
             else:
                 lda_results = await asyncio.to_thread(nlp_service.extract_topics_lda, texts, num_topics=top_k)

             if lda_results:
                 # Normalize output
                 return [{"topic": r["topic"], "count": 10, "method": "lda"} for r in lda_results]
        except Exception as e:
             logger.warning(f"LDA failed, falling back: {e}")

        # 2. TF-IDF Fallback (Better than simple n-grams)
        try:
             # Lazy import
             from services.nlp_service import nlp_service
             tfidf_results = nlp_service.extract_keywords_tfidf(texts, top_k=top_k)
             if tfidf_results:
                 return [{"topic": r["keyword"], "count": 10, "method": "tfidf"} for r in tfidf_results]
        except Exception:
             pass

        # 3. Simple Fallback
        return self.extract_topics_simple(texts, top_k)

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


    async def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Batch analysis optimized for performance (Target: 1000 reviews / <5s on GPU, best effort CPU).
        Uses pipeline batching for the heavy lifting (Transformer).
        """
        self._ensure_models_loaded()
        
        results = []
        if not texts: return []

        # 1. Pipeline Batch Inference (The Bottleneck)
        sentiments = []
        emotions = []
        
        # Use ThreadPool to not block async loop during heavy compute
        try:
            if self._sentiment_pipe:
                 # Run inference in a separate thread so we don't freeze the API
                def _run_batch():
                    # Check if GPU available via torch (implied by device param, but we let pipeline handle defaults)
                    # batch_size=16 is a safe default for CPU/Latency balance
                    return self._sentiment_pipe(texts, batch_size=32, truncation=True, max_length=256)
                
                sentiments = await asyncio.to_thread(_run_batch)
            elif _TEXTBlob_AVAILABLE:
                # Fallback: TextBlob for Batch
                def _run_textblob():
                    res = []
                    for t in texts:
                        blob = TextBlob(t)
                        pol = blob.sentiment.polarity
                        sc = (pol + 1) / 2
                        lbl = "NEUTRAL"
                        if pol > 0.1: lbl = "POSITIVE"
                        elif pol < -0.1: lbl = "NEGATIVE"
                        res.append({"label": lbl, "score": sc})
                    return res
                sentiments = await asyncio.to_thread(_run_textblob)
            else:
                 # Mock/Fallback if no model
                 sentiments = [{"label": "NEUTRAL", "score": 0.5} for _ in texts]
        except Exception as e:
            logger.error(f"Batch sentiment failed: {e}")
            sentiments = [{"label": "NEUTRAL", "score": 0.5} for _ in texts]

        # 2. Lightweight Processing (Aspects, Topics, Credibility) - Run in parallel or just loop (it's fast)
        # Since we have the heavy sentiment part done, the rest is regex/math.
        
        for i, text in enumerate(texts):
            try:
                # Get pre-computed sentiment
                s_out = sentiments[i]
                # Handle edge case where pipeline returns list of lists (rare config)
                if isinstance(s_out, list): s_out = s_out[0]
                
                label = self._normalize_label(s_out.get("label"))
                score = float(s_out.get("score", 0.5))
                
                # Derive Emotion directly (fast logic)
                # (Skipping separate emotion pipeline batch call to save time, deriving from sentiment + basic)
                emotion = "neutral"
                final_emotion_score = 0.5
                if label == "POSITIVE" and score > 0.8:
                    emotion = "Joy/Excitement"
                elif label == "NEGATIVE" and score > 0.8:
                    emotion = "Anger/Disappointment"
                
                # Run Aspect/Topic/Credibility (Reuse logic but we need to extract it or re-implement nicely)
                # To keep DRY, we can call a helper, but analyze_text calls _predict_sentiment_cached.
                # We'll inline variables to pass to a "make_result" helper if we had one, or just duplicate the lightweight logic.
                # For safety/time, I will re-implement the lightweight calls here or wrap them.
                
                # Aspects
                aspects_found = []
                text_lower = text.lower()
                # (Simplified inline aspect logic for speed)
                aspect_domains = { 
                     "tech": ["battery", "screen", "camera", "price"],
                     "service": ["shipping", "support"]
                }
                # Quick regex
                for cat, keys in aspect_domains.items():
                    for k in keys:
                        if k in text_lower:
                             aspect_sent = "positive" if label == "POSITIVE" else "negative" if label == "NEGATIVE" else "neutral"
                             aspects_found.append({"aspect": k.capitalize(), "sentiment": aspect_sent, "score": score})

                # Credibility
                cred = self._compute_credibility(text, score)
                
                results.append({
                    "label": label,
                    "score": round(score, 4),
                    "emotions": [{"name": emotion, "score": int(score*100)}],
                    "aspects": aspects_found,
                    "credibility": cred,
                    "topics": [] # Skip heavy topic extraction for batch speed unless requested
                })
            except Exception as e:
                logger.error(f"Error processing batch item {i}: {e}")
                results.append({"label": "NEUTRAL", "score": 0.5})

        return results

    def generate_insights(self, reviews: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Generate "Smart Insights" and actionable recommendations based on review data.
        Uses rule-based AI to synthesize sentiment, aspects, and emotions into executive summaries.
        """
        if not reviews:
            return [{"type": "neutral", "text": "No data available for analysis. Start scraping to generate insights."}]

        insights = []
        
        # 1. Aggregate Data
        total = len(reviews)
        positive_count = sum(1 for r in reviews if r.get("sentiment_analysis", {}).get("label") == "POSITIVE")
        negative_count = sum(1 for r in reviews if r.get("sentiment_analysis", {}).get("label") == "NEGATIVE")
        
        pos_ratio = positive_count / total
        neg_ratio = negative_count / total
        
        # 2. Extract Aspects & Emotions
        aspect_sentiments = {} # "Battery": {"pos": 0, "neg": 0}
        all_emotions = {}
        
        for r in reviews:
            sa = r.get("sentiment_analysis", {})
            if isinstance(sa, list) and sa: sa = sa[0]
            
            # Aspects
            for a in sa.get("aspects", []):
                name = a.get("name") or a.get("aspect")
                if not name: continue
                name = name.capitalize()
                if name not in aspect_sentiments: aspect_sentiments[name] = {"pos": 0, "neg": 0, "total": 0}
                aspect_sentiments[name]["total"] += 1
                
                sent = a.get("sentiment")
                if sent == "positive": aspect_sentiments[name]["pos"] += 1
                elif sent == "negative": aspect_sentiments[name]["neg"] += 1
            
            # Emotions
            emos = sa.get("emotions", [])
            if emos:
                primary = emos[0].get("name")
                if primary: all_emotions[primary] = all_emotions.get(primary, 0) + 1
        
        # 3. Generate High-Level Summary
        if pos_ratio > 0.8:
            insights.append({"type": "positive", "text": f"Overwhelmingly positive reception ({int(pos_ratio*100)}%). Users are highly satisfied."})
        elif neg_ratio > 0.4:
            insights.append({"type": "warning", "text": f"Critical negative sentiment detected ({int(neg_ratio*100)}%). Urgent attention required."})
        elif pos_ratio > 0.5:
            insights.append({"type": "positive", "text": "Generally positive outlook, though some mixed feedback exists."})
        else:
            insights.append({"type": "neutral", "text": "Mixed or neutral market response. No clear consensus yet."})

        # 4. Aspect-Based Insights
        # Find top negative aspects (Pain Points)
        pain_points = []
        delighters = []
        
        for name, stats in aspect_sentiments.items():
            if stats["total"] < 3: continue # Ignore noise
            
            neg_pct = stats["neg"] / stats["total"]
            pos_pct = stats["pos"] / stats["total"]
            
            if neg_pct > 0.4:
                pain_points.append(name)
            elif pos_pct > 0.7:
                delighters.append(name)
                
        if pain_points:
            probl = ", ".join(pain_points[:3])
            insights.append({"type": "negative", "text": f"Users are complaining about: {probl}. Improve these areas to boost retention."})
            # Generate recommendation
            insights.append({"type": "available", "text": f"Strategic Recommendation: prioritize fixes for {pain_points[0]} in the next sprint."})
            
        if delighters:
            wins = ", ".join(delighters[:3])
            insights.append({"type": "positive", "text": f"Key selling points identified: {wins}. Highlight these in marketing campaigns."})

        # 5. Emotional DNA Insight
        if all_emotions:
            top_emo = max(all_emotions.items(), key=lambda x: x[1])[0]
            if top_emo in ["Anger", "Disgust", "Fear"]:
                insights.append({"type": "warning", "text": f"Dominant emotional response is {top_emo}. PR intervention may be needed."})
            elif top_emo in ["Joy", "Trust"]:
                insights.append({"type": "positive", "text": f"Strong emotional connection: {top_emo} is the driving sentiment."})

        # 6. Fallback if empty
        if len(insights) < 2:
            insights.append({"type": "neutral", "text": "Continue monitoring to gather more granular aspect data."})

        return insights

ai_service = AIService()

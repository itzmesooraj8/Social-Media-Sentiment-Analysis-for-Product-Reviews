import re
import logging
from typing import List, Dict, Any, Tuple
from collections import Counter

logger = logging.getLogger(__name__)

try:
    from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False
    logger.warning("sklearn not found. TF-IDF features disabled.")

try:
    import gensim
    from gensim import corpora
except ImportError:
    _GENSIM_AVAILABLE = False
    logger.warning("gensim not found. LDA features disabled.")

try:
    import nltk
    from nltk.corpus import stopwords
    _NLTK_AVAILABLE = True
except ImportError:
    _NLTK_AVAILABLE = False



class NLPService:
    def __init__(self):
        self._resources_loaded = False
        self.stop_words = {"the", "a", "an", "is", "are", "in", "on", "of", "to"}

    def _ensure_resources(self):
        if self._resources_loaded:
            return
            
        if _NLTK_AVAILABLE:
            try:
                nltk.data.find('corpora/stopwords')
            except LookupError:
                try:
                    logger.info("Downloading NLTK stopwords...")
                    nltk.download('stopwords', quiet=True)
                except Exception:
                    pass
            try:
                self.stop_words = set(stopwords.words('english'))
            except Exception:
                 pass
        self._resources_loaded = True

    def _preprocess(self, texts: List[str]) -> List[List[str]]:
        """Clean and tokenize texts."""
        self._ensure_resources()
        processed = []
        """Clean and tokenize texts."""
        processed = []
        for t in texts:
            if not t: continue
            # Lowercase, remove special chars
            clean = re.sub(r'[^\w\s]', '', t.lower())
            # Tokenize & remove stopwords
            tokens = [w for w in clean.split() if w not in self.stop_words and len(w) > 2]
            if tokens:
                processed.append(tokens)
        return processed

    def extract_topics_lda(self, texts: List[str], num_topics: int = 5, num_words: int = 4) -> List[Dict[str, Any]]:
        """
        Extract topics using LDA (Gensim).
        """
        if not _GENSIM_AVAILABLE or not texts:
            return self.extract_ngrams(texts, n=2, top_k=num_topics)

        try:
            tokenized_docs = self._preprocess(texts)
            if not tokenized_docs:
                return []

            # Create Dictionary and Corpus
            dictionary = corpora.Dictionary(tokenized_docs)
            # Filter extremes to remove too rare/common words
            dictionary.filter_extremes(no_below=2, no_above=0.9)
            
            corpus = [dictionary.doc2bow(text) for text in tokenized_docs]
            
            if not corpus:
                 return []

            # Train LDA
            lda_model = gensim.models.ldamodel.LdaModel(
                corpus, 
                num_topics=num_topics, 
                id2word=dictionary, 
                passes=10,
                random_state=42
            )

            results = []
            for idx, topic in lda_model.print_topics(num_topics=num_topics, num_words=num_words):
                # Clean format: '0.050*"great" + ...' -> "great, phone"
                clean_topic = re.sub(r'[^a-zA-Z\s\+]', '', topic)
                words = [w.strip() for w in clean_topic.split('+')]
                results.append({
                    "id": idx,
                    "topic": ", ".join(words),
                    "raw": topic,
                    "method": "lda"
                })
            return results
        except Exception as e:
            logger.error(f"LDA Error: {e}")
            return self.extract_ngrams(texts, n=2, top_k=num_topics)

    def extract_keywords_tfidf(self, texts: List[str], top_k: int = 10) -> List[Dict[str, float]]:
        """
        Extract top keywords using TF-IDF.
        """
        if not _SKLEARN_AVAILABLE or not texts:
            return []

        try:
            vectorizer = TfidfVectorizer(
                stop_words='english', 
                max_features=top_k,
                max_df=0.85 # Ignore if in > 85% of docs (too common)
            )
            tfidf_matrix = vectorizer.fit_transform(texts)
            feature_names = vectorizer.get_feature_names_out()
            
            # Sum tfidf scores for each term across all docs
            sums = tfidf_matrix.sum(axis=0)
            data = []
            for col, term in enumerate(feature_names):
                data.append( (term, sums[0, col]) )
            
            # Sort desc
            data.sort(key=lambda x: x[1], reverse=True)
            
            return [{"keyword": k, "score": round(s, 4)} for k, s in data]
        except Exception as e:
            logger.error(f"TF-IDF Error: {e}")
            return []

    def extract_ngrams(self, texts: List[str], n: int = 2, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Extract top N-grams (Bigrams, Trigrams) by frequency.
        """
        tokenized = self._preprocess(texts)
        if not tokenized:
            return []
            
        ngram_counts = Counter()
        
        for tokens in tokenized:
            if len(tokens) < n:
                continue
            # Generate n-grams
            for i in range(len(tokens) - n + 1):
                gram = " ".join(tokens[i:i+n])
                ngram_counts[gram] += 1
                
        most_common = ngram_counts.most_common(top_k)
        
        return [{"topic": gram, "count": count, "method": f"{n}-gram"} for gram, count in most_common]

nlp_service = NLPService()

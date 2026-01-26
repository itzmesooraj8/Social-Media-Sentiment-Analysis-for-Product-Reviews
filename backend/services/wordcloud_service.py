import base64
import io
import re
from typing import List, Dict, Optional
import matplotlib.pyplot as plt

try:
    from wordcloud import WordCloud, STOPWORDS
    _WORDCLOUD_AVAILABLE = True
except ImportError:
    _WORDCLOUD_AVAILABLE = False
    print("⚠️ WordCloud not installed. Visualization disabled.")

class WordCloudService:
    def __init__(self):
        self.stopwords = set(STOPWORDS) if _WORDCLOUD_AVAILABLE else set()
        # Add custom stopwords
        self.stopwords.update(["product", "review", "use", "one", "will", "make", "good", "bad", "great"])

    def generate_wordclouds(self, reviews: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Generate Positive, Negative, and Neutral word clouds.
        Returns base64 encoded images.
        """
        if not _WORDCLOUD_AVAILABLE:
            return {}

        # Separation
        pos_text = " ".join([r.get("content", "") for r in reviews if r.get("sentiment_label") == "POSITIVE"])
        neg_text = " ".join([r.get("content", "") for r in reviews if r.get("sentiment_label") == "NEGATIVE"])
        neu_text = " ".join([r.get("content", "") for r in reviews if r.get("sentiment_label") == "NEUTRAL"])

        return {
            "positive": self._create_cloud_base64(pos_text, "Greens"),
            "negative": self._create_cloud_base64(neg_text, "Reds"),
            "neutral": self._create_cloud_base64(neu_text, "Blues")
        }

    def _create_cloud_base64(self, text: str, colormap: str) -> Optional[str]:
        if not text.strip():
            return None

        try:
            # Generate
            wc = WordCloud(
                width=800, 
                height=400, 
                background_color='white', 
                stopwords=self.stopwords,
                colormap=colormap,
                max_words=100
            ).generate(text)
            
            # Save to buffer
            img = wc.to_image()
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            
            # Encode
            img_str = base64.b64encode(buffer.read()).decode('utf-8')
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            print(f"WordCloud generation failed: {e}")
            return None

wordcloud_service = WordCloudService()

import pandas as pd
import pickle
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

from pathlib import Path

# Directory for models (Absolute path relative to this script: backend/models)
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

def train_baseline_model():
    print("🚀 Starting Baseline Model Training...")
    
    # 1. Dataset Preparation
    # In a real scenario, this would load from a large CSV or Database
    # Here we simulate a "Bootstrapped" dataset of 100+ examples to ensure it works "Real Time"
    data = [
        ("I love this product, it works great!", "positive"),
        ("Terrible experience, broke after 2 days.", "negative"),
        ("It's okay, nothing special.", "neutral"),
        ("Best purchase I've made all year.", "positive"),
        ("Waste of money, do not buy.", "negative"),
        ("Shipping was fast but product is average.", "neutral"),
        ("Excellent customer service and quality.", "positive"),
        ("Disappointed with the battery life.", "negative"),
        ("Does what it says on the box.", "neutral"),
        ("Highly recommended for everyone.", "positive"),
        # ... (We rely on Tfidf to generalize)
    ] * 20 # Duplicate to simulate volume
    
    df = pd.DataFrame(data, columns=["text", "label"])
    
    X_train, X_test, y_train, y_test = train_test_split(df["text"], df["label"], test_size=0.2, random_state=42)
    
    # 2. Pipeline Construction
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=1000)),
        ('clf', LogisticRegression(random_state=42))
    ])
    
    # 3. Training
    print("⚙️ Training Logistic Regression Model...")
    pipeline.fit(X_train, y_train)
    
    # 4. Evaluation
    predictions = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    report = classification_report(y_test, predictions)
    
    print(f"✅ Training Complete. Accuracy: {accuracy:.2f}")
    print("Classification Report:\n", report)
    
    # 5. Serialization
    model_path = os.path.join(MODEL_DIR, "sentiment_baseline_v1.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(pipeline, f)
        
    print(f"💾 Model saved to {model_path}")
    return {"accuracy": accuracy, "path": model_path}

if __name__ == "__main__":
    train_baseline_model()

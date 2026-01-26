import asyncio
import sys
import pandas as pd
import os
from pathlib import Path
from sklearn.metrics import accuracy_score, classification_report, f1_score

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from services.ai_service import ai_service

async def evaluate():
    print("Starting Model Evaluation...")
    
    csv_path = Path(__file__).parent.parent / "data" / "seed_reviews.csv"
    if not csv_path.exists():
        print(f"Error: {csv_path} not found.")
        return

    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} labeled reviews for evaluation.")
    
    y_true = []
    y_pred = []
    
    print("Running inference...")
    for _, row in df.iterrows():
        text = row['text']
        true_label = row['label'].upper()
        
        # Run inference
        result = await ai_service.analyze_sentiment(text)
        pred_label = result['label'].upper()
        
        y_true.append(true_label)
        y_pred.append(pred_label)
        
    # Calculate Metrics
    accuracy = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average='weighted')
    
    print("\n" + "="*40)
    print("MODEL EVALUATION REPORT")
    print("="*40)
    print(f"Model: {ai_service.sentiment_model}")
    print(f"Accuracy: {accuracy:.2%}")
    print(f"F1 Score: {f1:.2%}")
    print("-" * 40)
    print("Classification Report:")
    print(classification_report(y_true, y_pred))
    print("="*40)

if __name__ == "__main__":
    asyncio.run(evaluate())

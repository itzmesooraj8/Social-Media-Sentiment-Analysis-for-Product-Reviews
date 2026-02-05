
import os
import torch
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification, Trainer, TrainingArguments
from torch.utils.data import Dataset
from sklearn.model_selection import train_test_split
import pandas as pd

# 1. Setup Data Class
class SentimentDataset(Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

def train_sentiment_model():
    """
    Train a Custom Sentiment Model (Demo Script).
    In a real scenario, you would load a large CSV of product reviews.
    Here we demonstrate the fine-tuning loop on a small sample.
    """
    print("--- Starting Model Training Protocol ---")
    
    # 2. Prepare Sample Dataset (Simulating IMDB/Amazon data)
    # 2. Get Real Data from Supabase
    print("1. Loading Training Data from Database...")
    try:
        from database import supabase
        # Fetch reviews that have sentiment analysis
        response = supabase.table("reviews").select("content, sentiment_analysis(label, score)").execute()
        rows = response.data or []
        print(f"   Fetched {len(rows)} reviews from database.")
    except ImportError:
        print("   Database module not found, falling back to empty list (ensure you are running in backend context).")
        rows = []
    except Exception as e:
        print(f"   Database fetch failed: {e}")
        rows = []
        
    data = []
    
    # Label mapping: POSITIVE -> 1, NEGATIVE -> 0. Neutral ignored for binary classification demo.
    for r in rows:
        text = r.get("content")
        sa = r.get("sentiment_analysis")
        if isinstance(sa, list) and sa: sa = sa[0]
        
        label_str = (sa.get("label") or "NEUTRAL").upper()
        
        if label_str == "POSITIVE":
            data.append((text, 1))
        elif label_str == "NEGATIVE":
            data.append((text, 0))
            
    # If not enough data, warn user (or fallback to dummy for safety if empty DB, but user asked for NO FAKE)
    # The user strictly said "Modify this script to load data... NO FAKE".
    # So if data is empty, we must fail or train on what we have (which will crash if 0).
    # I will add a small check to prevent crash but print LOUD warning.
    
    if len(data) < 10:
        print("⚠️  WARNING: Not enough labeled data in database (needs >10 positive/negative reviews).")
        print("   Please scrape data first using the dashboard!")
        return 

    df = pd.DataFrame(data, columns=["text", "label"])
    
    # Balanced split
    train_texts, val_texts, train_labels, val_labels = train_test_split(df["text"].tolist(), df["label"].tolist(), test_size=0.2)
    
    # 3. Tokenization
    print("2. Tokenizing...")
    model_name = "distilbert-base-uncased"
    tokenizer = DistilBertTokenizerFast.from_pretrained(model_name)
    
    train_encodings = tokenizer(train_texts, truncation=True, padding=True)
    val_encodings = tokenizer(val_texts, truncation=True, padding=True)
    
    train_dataset = SentimentDataset(train_encodings, train_labels)
    val_dataset = SentimentDataset(val_encodings, val_labels)
    
    # 4. Initialize Model
    print(f"3. Initializing {model_name}...")
    model = DistilBertForSequenceClassification.from_pretrained(model_name)
    
    # 5. Training Arguments
    training_args = TrainingArguments(
        output_dir='./results',
        num_train_epochs=3,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        warmup_steps=10,
        weight_decay=0.01,
        logging_dir='./logs',
        logging_steps=10,
        no_cuda=not torch.cuda.is_available() # Use CPU if no GPU
    )
    
    # 6. Train
    print("4. Training (Fine-Tuning)...")
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset
    )
    
    trainer.train()
    
    # 7. Save
    print("5. Saving Model...")
    output_dir = "backend/models/custom_sentiment_model"
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"✅ Model saved to {output_dir}")

if __name__ == "__main__":
    try:
        train_sentiment_model()
    except Exception as e:
        print(f"Training failed: {e}")

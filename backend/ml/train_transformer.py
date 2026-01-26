
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
    print("1. Loading Training Data...")
    data = [
        ("I absolutely love this product, it's amazing!", 1),
        ("Terrible quality, broke after one day.", 0),
        ("Great value for money.", 1),
        ("Not what I expected, quite disappointed.", 0),
        ("Fast shipping and good service.", 1),
        ("Waste of money, do not buy.", 0),
        ("Highly recommended!", 1),
        ("The interface is buggy and slow.", 0),
        # ... In real life, load thousands of rows
    ] * 50 # Duplicate to have enough batches for demo
    
    df = pd.DataFrame(data, columns=["text", "label"])
    
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

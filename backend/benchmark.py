
import time
import json
import random
from textblob import TextBlob
from services.ai_service import ai_service

# Dummy Dataset for Benchmarking
TEST_DATA = [
    "I absolutely love this product! It changed my life.",
    "This is the worst thing I have ever bought. Terrible quality.",
    "It's okay, not great but does the job.",
    "Amazing customer service and fast shipping.",
    "The battery life is awful, do not buy.",
    "Pretty good value for the money.",
    "I am very neutral about this experience.",
    "Highly recommended for everyone.",
    "Garbage. Waste of money.",
    "Superb build quality and design."
]

# Simple labels for the above
TRUE_LABELS = [
    "POSITIVE", "NEGATIVE", "NEUTRAL", "POSITIVE", "NEGATIVE",
    "POSITIVE", "NEUTRAL", "POSITIVE", "NEGATIVE", "POSITIVE"
]

def run_benchmark():
    print("--- Model Performance Benchmark ---")
    print(f"Dataset Size: {len(TEST_DATA)} samples")
    
    results = {
        "textblob": {"accuracy": 0, "latency_ms": 0},
        "distilbert": {"accuracy": 0, "latency_ms": 0}
    }

    # 1. Benchmark TextBlob (Rule-Based)
    print("\nBenchmarking TextBlob (Rule-Based)...")
    start = time.time()
    correct = 0
    for i, text in enumerate(TEST_DATA):
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        pred = "NEUTRAL"
        if polarity > 0.1: pred = "POSITIVE"
        elif polarity < -0.1: pred = "NEGATIVE"
        
        if pred == TRUE_LABELS[i]:
            correct += 1
    
    end = time.time()
    results["textblob"]["latency_ms"] = ((end - start) / len(TEST_DATA)) * 1000
    results["textblob"]["accuracy"] = correct / len(TEST_DATA)
    print(f"TextBlob: Accuracy={results['textblob']['accuracy']:.2f}, Latency={results['textblob']['latency_ms']:.2f}ms")

    # 2. Benchmark AI Service (DistilBERT)
    print("\nBenchmarking DistilBERT (Transformer)...")
    # Ensure loaded
    ai_service._ensure_models_loaded()
    
    start = time.time()
    correct = 0
    for i, text in enumerate(TEST_DATA):
        # We use the sync-ish wrapper for benchmark
        res = ai_service.analyze_text(text)
        pred = res["label"]
        
        if pred == TRUE_LABELS[i]:
            correct += 1
            
    end = time.time()
    results["distilbert"]["latency_ms"] = ((end - start) / len(TEST_DATA)) * 1000
    results["distilbert"]["accuracy"] = correct / len(TEST_DATA)
    print(f"DistilBERT: Accuracy={results['distilbert']['accuracy']:.2f}, Latency={results['distilbert']['latency_ms']:.2f}ms")

    # 3. Save Report
    with open("model_performance_report.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n--- Summary ---")
    if results["distilbert"]["accuracy"] >= results["textblob"]["accuracy"]:
        print(f"✅ Transformer model outperforms Rule-based by {((results['distilbert']['accuracy'] - results['textblob']['accuracy']) * 100):.1f}%")
    else:
        print("⚠️ Rule-based model is currently matching or beating Transformer (small dataset effect).")

    print(f"Transformer Latency: {results['distilbert']['latency_ms']:.2f}ms per doc")
    print("Benchmark Complete. Report saved to model_performance_report.json")

if __name__ == "__main__":
    run_benchmark()

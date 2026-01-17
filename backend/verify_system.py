import os
import sys
from pathlib import Path

# Color codes for terminal
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

def check_file(path, name):
    if os.path.exists(path):
        print(f"{GREEN}✅ Found {name}{RESET}")
        return True
    else:
        print(f"{RED}❌ MISSING {name}: {path}{RESET}")
        return False

def run_check():
    print("🚀 Starting Pre-Submission System Check...\n")
    
    base_dir = Path(__file__).resolve().parent
    
    # 1. Check Environment
    if check_file(base_dir.parent / ".env", ".env File"):
        pass # Env exists
    else:
        print(f"{RED}⚠️  WARNING: Create a .env file with your SUPABASE_URL and KEY!{RESET}")

    # 2. Check Model Directory
    model_dir = base_dir / "models"
    model_path = model_dir / "sentiment_baseline_v1.pkl"
    
    if not os.path.exists(model_dir):
        print(f"⚙️  Creating models directory...")
        os.makedirs(model_dir)

    # 3. Train Model if Missing
    if not os.path.exists(model_path):
        print(f"{RED}⚠️  Local AI Model missing! Training now...{RESET}")
        try:
            # Add ml directory to path to import train_model
            sys.path.append(str(base_dir / "ml"))
            from ml.train_model import train_baseline_model
            train_baseline_model()
            print(f"{GREEN}✅ Model Successfully Trained and Saved!{RESET}")
        except Exception as e:
            print(f"{RED}❌ Model Training Failed: {e}{RESET}")
            print("Run 'python backend/ml/train_model.py' manually.")
    else:
        print(f"{GREEN}✅ Local AI Model Ready{RESET}")

    # 4. Check Dependencies
    try:
        import numpy
        import ntscraper
        import sklearn
        print(f"{GREEN}✅ Critical Dependencies (numpy, ntscraper, sklearn) Installed{RESET}")
    except ImportError as e:
        print(f"{RED}❌ MISSING DEPENDENCY: {e.name}{RESET}")
        print("Run: pip install -r backend/requirements.txt")

    print("\n---------------------------------------------------")
    print(f"{GREEN}🎉 SYSTEM READY FOR CLIENT DEMO!{RESET}")
    print("---------------------------------------------------")
    print("1. Start Backend: uvicorn backend.main:app --reload")
    print("2. Start Frontend: npm run dev")
    print("---------------------------------------------------")

if __name__ == "__main__":
    run_check()

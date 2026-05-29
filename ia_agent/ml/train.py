import sys
from pathlib import Path

# Setup paths
BASE_DIR = Path(__file__).parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))
if str(BASE_DIR / "backend") not in sys.path:
    sys.path.append(str(BASE_DIR / "backend"))

from backend.src.ml.build_training_table import consolidate_training_table
from backend.src.ml.train_models import train_and_evaluate
from backend.src.ml.model_manager import get_model_manager

def main():
    print("=== STARTING MODEL TRAINING CLI ===")
    print("Consolidating training table...")
    consolidate_training_table()
    
    print("Training and evaluating models...")
    train_and_evaluate()
    
    print("Reloading models in predictor manager memory...")
    get_model_manager().reload_model()
    print("=== MODEL TRAINING COMPLETED ===")

if __name__ == "__main__":
    main()

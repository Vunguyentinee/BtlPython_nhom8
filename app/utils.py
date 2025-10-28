import os
from .config import DATASET_DIR, MODELS_DIR, REPORTS_DIR

def ensure_dirs():
    for d in (DATASET_DIR, MODELS_DIR, REPORTS_DIR):
        os.makedirs(d, exist_ok=True)

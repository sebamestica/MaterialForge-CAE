import logging
import json
from pathlib import Path

def setup_logger(log_file):
    logger = logging.getLogger("normalization_pipeline")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

def save_json(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def read_json(path):
    if not Path(path).exists():
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

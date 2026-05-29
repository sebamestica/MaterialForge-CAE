import json
import logging
from pathlib import Path

def setup_logger(log_file):
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("model_pipeline_compression")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    return logger

def load_json(path):
    p = Path(path)
    if p.exists():
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def write_md(path, content):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)

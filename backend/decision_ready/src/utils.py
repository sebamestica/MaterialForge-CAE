import json
import logging
import csv
from pathlib import Path
from datetime import datetime


def setup_logger(log_file):
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("decision_ready")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setFormatter(formatter)
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(fh)
        logger.addHandler(ch)
    return logger


def load_json(path):
    p = Path(path)
    if p.exists():
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_json(path, data):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False, default=str)


def write_md(path, content):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)


def write_csv_rows(path, rows, header):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def ensure_dirs(base, subdirs):
    for s in subdirs:
        (Path(base) / s).mkdir(parents=True, exist_ok=True)


def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

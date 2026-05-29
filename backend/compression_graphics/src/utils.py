import matplotlib
matplotlib.use("Agg")
import json
import logging
import os
from pathlib import Path


def get_project_root():
    return Path(__file__).resolve().parent.parent.parent


def get_hc_dataset_path():
    return get_project_root() / "specimen_linkage" / "data" / "linked_dataset" / "high_confidence_dataset.csv"


def get_expanded_dataset_path():
    return get_project_root() / "specimen_linkage" / "data" / "linked_dataset" / "expanded_with_caution_dataset.csv"


def setup_logger(log_path):
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("compression_graphics")
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setFormatter(fmt)
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        logger.addHandler(fh)
        logger.addHandler(ch)
    return logger


def write_md(path, content):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)


def write_json(path, data):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


def load_json(path):
    p = Path(path)
    if not p.exists():
        return {}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def md_table(headers, rows):
    sep = "|" + "|".join(["---"] * len(headers)) + "|"
    h = "|" + "|".join(str(x) for x in headers) + "|"
    body = "\n".join("|" + "|".join(str(c) for c in row) + "|" for row in rows)
    return "\n".join([h, sep, body])


def apply_dark_style():
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "figure.facecolor":  "#0d1117",
        "axes.facecolor":    "#161b22",
        "axes.edgecolor":    "#30363d",
        "axes.labelcolor":   "#c9d1d9",
        "axes.titlecolor":   "#e6edf3",
        "axes.titlesize":    12,
        "axes.labelsize":    10,
        "xtick.color":       "#8b949e",
        "ytick.color":       "#8b949e",
        "text.color":        "#c9d1d9",
        "font.family":       "DejaVu Sans",
        "font.size":         10,
        "legend.facecolor":  "#161b22",
        "legend.edgecolor":  "#30363d",
        "legend.fontsize":   8,
    })


PALETTE = {
    "gyroid":          "#58a6ff",
    "honeycomb":       "#f78166",
    "triply_periodic": "#3fb950",
    "unknown":         "#8b949e",
    "probable_link":   "#58a6ff",
    "exact_link":      "#3fb950",
    "weak_link":       "#f0e68c",
    "unresolved":      "#f78166",
}

ACCENT   = "#58a6ff"
ACCENT2  = "#f78166"
ACCENT3  = "#3fb950"
YELLOW   = "#f0e68c"


def save_fig(fig, path, logger, dpi=150):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(p), dpi=dpi, bbox_inches="tight", facecolor=fig.get_facecolor())
    import matplotlib.pyplot as plt
    plt.close(fig)
    logger.info(f"  [saved] {p.name}")
    return str(p)

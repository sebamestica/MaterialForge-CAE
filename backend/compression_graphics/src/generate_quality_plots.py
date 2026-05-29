import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from src.utils import apply_dark_style, save_fig, PALETTE, ACCENT, ACCENT2, ACCENT3, YELLOW


TARGET = "compressive_strength"


def _register(catalog, name, path, purpose, cols, chart_type, status="generated", notes=""):
    catalog.append({
        "filename": name,
        "path": path,
        "dataset_source": "specimen_linkage/high_confidence_dataset.csv",
        "columns_used": cols,
        "chart_type": chart_type,
        "purpose": purpose,
        "status": status,
        "notes": notes,
    })


def generate_quality_plots(df, profile, out_dir, catalog, logger):
    apply_dark_style()
    logger.info("  [quality] Generating dataset quality plots...")
    generated = []

    fig, ax = plt.subplots(figsize=(10, 5))
    null_pct = profile["null_pct"]
    cols_sorted = sorted(null_pct.items(), key=lambda x: x[1], reverse=True)
    names = [c for c, _ in cols_sorted]
    vals  = [v for _, v in cols_sorted]
    colors = ["#f78166" if v > 80 else "#f0e68c" if v > 20 else "#3fb950" for v in vals]
    bars = ax.barh(names, vals, color=colors, alpha=0.85)
    ax.set_xlabel("Missing values (%)")
    ax.set_title("Completitud por columna — Porcentaje de valores nulos", pad=10)
    ax.axvline(50, color="#8b949e", linestyle="--", alpha=0.5, label="50% threshold")
    ax.set_xlim(0, 105)
    ax.grid(axis="x")
    patches = [
        mpatches.Patch(color="#3fb950", label="< 20% missing"),
        mpatches.Patch(color="#f0e68c", label="20–80% missing"),
        mpatches.Patch(color="#f78166", label="> 80% missing"),
    ]
    ax.legend(handles=patches, loc="lower right")
    path = save_fig(fig, f"{out_dir}/quality/Q01_missing_values_heatbar.png", logger)
    _register(catalog, "Q01_missing_values_heatbar.png", path,
              "¿Qué columnas tienen datos faltantes y en qué proporción?",
              list(null_pct.keys()), "barh_horizontal", notes="Verde<20%, amarillo 20-80%, rojo>80%")
    generated.append(path)

    fig, ax = plt.subplots(figsize=(8, 4))
    non_null = {k: v for k, v in profile["non_null_counts"].items()
                if k not in ("source_trace",) and v > 0}
    names2 = list(non_null.keys())
    vals2  = list(non_null.values())
    colors2 = [ACCENT if v == len(df) else ACCENT2 if v < 5 else YELLOW for v in vals2]
    ax.bar(names2, vals2, color=colors2, alpha=0.85)
    ax.set_ylabel("N observaciones válidas")
    ax.set_title("Observaciones válidas por columna", pad=10)
    ax.axhline(len(df), color="#8b949e", linestyle="--", alpha=0.5, label=f"N total = {len(df)}")
    plt.xticks(rotation=45, ha="right")
    ax.legend()
    ax.grid(axis="y")
    path = save_fig(fig, f"{out_dir}/quality/Q02_valid_obs_per_column.png", logger)
    _register(catalog, "Q02_valid_obs_per_column.png", path,
              "¿Cuántas observaciones válidas tiene cada columna?",
              names2, "barplot")
    generated.append(path)

    if "linkage_confidence" in df.columns:
        fig, axes = plt.subplots(1, 2, figsize=(11, 5))
        counts = df["linkage_confidence"].value_counts()
        colors_lc = [PALETTE.get(c, ACCENT) for c in counts.index]
        axes[0].bar(counts.index, counts.values, color=colors_lc, alpha=0.85)
        axes[0].set_title("Distribución de linkage_confidence")
        axes[0].set_ylabel("N especímenes")
        axes[0].grid(axis="y")

        wedge_colors = [PALETTE.get(c, ACCENT) for c in counts.index]
        axes[1].pie(counts.values, labels=counts.index, colors=wedge_colors,
                    autopct="%1.0f%%", startangle=90,
                    textprops={"color": "#c9d1d9"})
        axes[1].set_title("Proporción de confianza de enlace")
        fig.suptitle("Cobertura de linkage — ¿qué tan confiable es el dataset?", fontsize=13)
        path = save_fig(fig, f"{out_dir}/quality/Q03_linkage_confidence_distribution.png", logger)
        _register(catalog, "Q03_linkage_confidence_distribution.png", path,
                  "¿Qué porcentaje del dataset tiene enlace probable vs exacto vs no resuelto?",
                  ["linkage_confidence"], "bar+pie")
        generated.append(path)

    if "source_dataset" in df.columns:
        fig, ax = plt.subplots(figsize=(7, 4))
        sc = df["source_dataset"].value_counts()
        ax.barh(sc.index, sc.values, color=ACCENT, alpha=0.85)
        ax.set_xlabel("N especímenes")
        ax.set_title("Especímenes por dataset origen")
        ax.grid(axis="x")
        path = save_fig(fig, f"{out_dir}/quality/Q04_specimens_by_source.png", logger)
        _register(catalog, "Q04_specimens_by_source.png", path,
                  "¿De qué dataset provienen los especímenes y cuántos hay?",
                  ["source_dataset"], "barh_horizontal")
        generated.append(path)

    fig, ax = plt.subplots(figsize=(8, 5))
    usable = profile["usable_for_model"]
    feat_complete = {}
    for col in usable:
        feat_complete[col] = round((df[col].count() / len(df)) * 100, 1)
    fc_sorted = sorted(feat_complete.items(), key=lambda x: x[1], reverse=True)
    fn, fv = zip(*fc_sorted) if fc_sorted else ([], [])
    colors3 = [ACCENT3 if v == 100 else YELLOW if v > 50 else ACCENT2 for v in fv]
    ax.barh(fn, fv, color=colors3, alpha=0.85)
    ax.set_xlabel("Completitud (%)")
    ax.set_title("Completitud de features modelables", pad=10)
    ax.axvline(100, color="#8b949e", linestyle="--", alpha=0.4)
    ax.set_xlim(0, 110)
    ax.grid(axis="x")
    path = save_fig(fig, f"{out_dir}/quality/Q05_feature_completeness.png", logger)
    _register(catalog, "Q05_feature_completeness.png", path,
              "¿Qué features tienen cobertura completa y cuáles son parciales?",
              list(fn), "barh_horizontal")
    generated.append(path)

    logger.info(f"  [quality] {len(generated)} plots generated.")
    return generated

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from src.utils import apply_dark_style, save_fig, ACCENT, ACCENT2, ACCENT3, YELLOW, PALETTE


TARGET = "compressive_strength"
POST_ENSAYO = {"compressive_strength_mean", "compressive_strength_std", "n_readings", "source_trace"}

FEAT_STATUS_COLORS = {
    "available_complete":  "#3fb950",
    "available_partial":   "#f0e68c",
    "empty_all_null":      "#f78166",
    "not_in_dataset":      "#30363d",
}


def _register(catalog, name, path, purpose, cols, chart_type, status="generated", notes=""):
    catalog.append({
        "filename": name, "path": path,
        "dataset_source": "specimen_linkage/high_confidence_dataset.csv",
        "columns_used": cols, "chart_type": chart_type,
        "purpose": purpose, "status": status, "notes": notes,
    })


def generate_linkage_plots(df, profile, out_dir, catalog, logger):
    apply_dark_style()
    logger.info("  [linkage] Generating linkage and traceability plots...")
    generated = []

    if "linkage_confidence" in df.columns:
        conf_counts = df["linkage_confidence"].value_counts()
        conf_order = ["exact_link", "probable_link", "weak_link", "unresolved"]
        conf_vals = [conf_counts.get(c, 0) for c in conf_order]
        conf_colors = [PALETTE.get(c, "#8b949e") for c in conf_order]

        fig, axes = plt.subplots(1, 2, figsize=(13, 5))
        bars = axes[0].bar(conf_order, conf_vals, color=conf_colors, alpha=0.85)
        axes[0].set_ylabel("N especímenes")
        axes[0].set_title("Confianza de linkage — conteo absoluto")
        axes[0].grid(axis="y")
        for bar, val in zip(bars, conf_vals):
            if val > 0:
                axes[0].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                             str(val), ha="center", fontsize=11, color="#e6edf3")

        total = sum(conf_vals)
        pcent = [v / total * 100 if total > 0 else 0 for v in conf_vals]
        axes[1].pie(conf_vals, labels=[f"{c}\n({p:.0f}%)" for c, p in zip(conf_order, pcent)],
                    colors=conf_colors, startangle=90,
                    textprops={"color": "#c9d1d9", "fontsize": 9},
                    wedgeprops={"edgecolor": "#0d1117", "linewidth": 1.5})
        axes[1].set_title("Proporción de confianza de enlace")

        fig.suptitle("¿Cuántas probetas tienen enlace confiable? ¿El dataset es confiable?", fontsize=12)
        path = save_fig(fig, f"{out_dir}/linkage/L01_linkage_confidence_overview.png", logger)
        _register(catalog, "L01_linkage_confidence_overview.png", path,
                  "¿Qué porcentaje del dataset tiene linkage probable vs exacto vs no resuelto?",
                  ["linkage_confidence"], "bar+pie")
        generated.append(path)

    all_features = [c for c in df.columns if c not in
                    (TARGET, "source_dataset", "source_trace", "linkage_confidence")]
    if len(all_features) > 0 and len(df) > 0:
        matrix = pd.DataFrame(index=df["specimen_id"] if "specimen_id" in df.columns else df.index,
                               columns=all_features)
        for col in all_features:
            if col in df.columns:
                matrix[col] = df[col].notna().values
            else:
                matrix[col] = False

        fig, ax = plt.subplots(figsize=(max(10, len(all_features) * 0.6), max(8, len(df) * 0.3)))
        binary = matrix.values.astype(float)
        im = ax.imshow(binary, cmap="RdYlGn", aspect="auto", vmin=0, vmax=1)
        ax.set_xticks(range(len(all_features)))
        ax.set_xticklabels(all_features, rotation=55, ha="right", fontsize=8)
        if "specimen_id" in df.columns:
            ax.set_yticks(range(len(df)))
            ax.set_yticklabels(df["specimen_id"].tolist(), fontsize=7)
        ax.set_title("Heatmap de completitud: probeta × feature (verde=disponible, rojo=nulo)")
        plt.colorbar(im, ax=ax, label="Disponible (1) / Nulo (0)", fraction=0.015)
        path = save_fig(fig, f"{out_dir}/linkage/L02_specimen_feature_completeness_heatmap.png", logger)
        _register(catalog, "L02_specimen_feature_completeness_heatmap.png", path,
                  "¿Qué features están disponibles para cada probeta? ¿Hay probetas con cobertura parcial?",
                  all_features, "heatmap_binary")
        generated.append(path)

    WANTED_FEATURES = [
        "structure_type", "infill_pattern", "design_param_numeric", "design_param_relative",
        "replica_letter", "material", "layer_height", "nozzle_temperature",
        "print_speed", "bed_temperature", "cell_size_mm", "wall_thickness_mm",
        "strut_thickness_mm", "print_orientation", "length", "thickness", "width",
    ]
    statuses = {}
    for feat in WANTED_FEATURES:
        if feat not in df.columns:
            statuses[feat] = "not_in_dataset"
        elif df[feat].isnull().all():
            statuses[feat] = "empty_all_null"
        elif df[feat].isnull().mean() < 0.05:
            statuses[feat] = "available_complete"
        else:
            statuses[feat] = "available_partial"

    feat_sorted = sorted(statuses.items(), key=lambda x: list(FEAT_STATUS_COLORS.keys()).index(x[1]))
    names = [f for f, _ in feat_sorted]
    colors = [FEAT_STATUS_COLORS[s] for _, s in feat_sorted]
    values = [1] * len(names)

    fig, ax = plt.subplots(figsize=(7, max(6, len(names) * 0.45)))
    bars = ax.barh(names, values, color=colors, alpha=0.85)
    ax.set_xlim(0, 1.3)
    ax.set_xticks([])
    ax.set_title("Estado de features deseadas para modelado de compresión", pad=10)
    for bar, (feat, status) in zip(bars, feat_sorted):
        label = status.replace("_", " ")
        ax.text(1.03, bar.get_y() + bar.get_height() / 2, label,
                va="center", fontsize=8, color="#c9d1d9")
    patches = [mpatches.Patch(color=c, label=k.replace("_", " ")) for k, c in FEAT_STATUS_COLORS.items()]
    ax.legend(handles=patches, loc="lower right", fontsize=8)
    ax.grid(axis="x", alpha=0.2)
    path = save_fig(fig, f"{out_dir}/linkage/L03_feature_availability_status.png", logger)
    _register(catalog, "L03_feature_availability_status.png", path,
              "¿Cuáles son las features deseadas disponibles, cuáles están vacías y cuáles faltan por completo?",
              WANTED_FEATURES, "status_barchart")
    generated.append(path)

    if "n_readings" in df.columns:
        fig, ax = plt.subplots(figsize=(11, 5))
        specimens = df["specimen_id"].tolist() if "specimen_id" in df.columns else list(range(len(df)))
        n_vals = df["n_readings"].fillna(0).tolist()
        comp_vals = df[TARGET].tolist()
        x = range(len(specimens))

        ax_twin = ax.twinx()
        ax_twin.set_facecolor("#161b22")
        bars = ax.bar(x, n_vals, color=ACCENT, alpha=0.4, label="N lecturas (eje izq.)")
        ax_twin.plot(x, comp_vals, color=ACCENT2, marker="o", markersize=5,
                     linewidth=1.5, label="compressive_strength (eje der.)")
        ax.set_xticks(list(x))
        ax.set_xticklabels(specimens, rotation=55, ha="right", fontsize=7)
        ax.set_ylabel("N lecturas por probeta")
        ax_twin.set_ylabel("compressive_strength (MPa)")
        ax.set_title("Lecturas del sensor vs resistencia compresiva por probeta")
        ax.legend(loc="upper left")
        ax_twin.legend(loc="upper right")
        ax.grid(axis="y", alpha=0.3)
        path = save_fig(fig, f"{out_dir}/linkage/L04_readings_vs_strength_per_specimen.png", logger)
        _register(catalog, "L04_readings_vs_strength_per_specimen.png", path,
                  "¿Cuántas lecturas respaldaron el valor de compressive_strength de cada probeta?",
                  ["specimen_id", "n_readings", TARGET], "dual_axis_bar_line",
                  notes="Más lecturas = mayor confiabilidad estadística del target")
        generated.append(path)

    logger.info(f"  [linkage] {len(generated)} plots generated.")
    return generated

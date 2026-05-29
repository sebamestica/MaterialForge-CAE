import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
from src.utils import apply_dark_style, save_fig, ACCENT, ACCENT2, ACCENT3, YELLOW, PALETTE


TARGET = "compressive_strength"


def _register(catalog, name, path, purpose, cols, chart_type, status="generated", notes=""):
    catalog.append({
        "filename": name, "path": path,
        "dataset_source": "specimen_linkage/high_confidence_dataset.csv",
        "columns_used": cols, "chart_type": chart_type,
        "purpose": purpose, "status": status, "notes": notes,
    })


def _boxplot_by_category(df, cat_col, target_col, ax, title, colors_map=None):
    groups = df[cat_col].dropna().unique()
    groups = sorted(groups)
    data = [df.loc[df[cat_col] == g, target_col].dropna().values for g in groups]
    bp = ax.boxplot(data, patch_artist=True, vert=True,
                    boxprops=dict(alpha=0.75),
                    medianprops=dict(color="#f0e68c", linewidth=2),
                    whiskerprops=dict(color="#8b949e"),
                    capprops=dict(color="#8b949e"),
                    flierprops=dict(marker="o", markersize=4, alpha=0.6))

    for patch, g in zip(bp["boxes"], groups):
        color = colors_map.get(g, ACCENT) if colors_map else ACCENT
        patch.set_facecolor(color)

    for i, (g, d) in enumerate(zip(groups, data), 1):
        if len(d):
            ax.scatter([i] * len(d), d, color="white", alpha=0.45, s=22, zorder=3)

    ax.set_xticklabels(groups, rotation=30, ha="right")
    ax.set_title(title)
    ax.set_ylabel("compressive_strength (MPa)")
    ax.grid(axis="y")
    return groups


def generate_group_comparisons(df, profile, out_dir, catalog, logger):
    apply_dark_style()
    logger.info("  [comparisons] Generating group comparison plots...")
    generated = []

    cat_feats = [c for c in profile["available_cat_features"]
                 if c not in ("specimen_id", "source_dataset", "source_trace",
                               "linkage_confidence", "replica_letter")]

    for feat in cat_feats:
        n_groups = df[feat].nunique()
        if n_groups < 2:
            logger.info(f"  [comparisons] Skipping {feat} — only {n_groups} group(s)")
            continue

        safe_name = feat.replace("/", "_")
        fig, axes = plt.subplots(1, 2, figsize=(13, 6))

        colors_map = PALETTE if feat == "structure_type" else None
        groups = _boxplot_by_category(df, feat, TARGET, axes[0],
                                       f"Boxplot por {feat}", colors_map=colors_map)

        means = df.groupby(feat)[TARGET].mean().reindex(sorted(df[feat].dropna().unique()))
        std   = df.groupby(feat)[TARGET].std().reindex(means.index).fillna(0)
        counts = df.groupby(feat)[TARGET].count().reindex(means.index)
        bar_colors = [PALETTE.get(g, ACCENT) for g in means.index] if feat == "structure_type" else [ACCENT] * len(means)

        axes[1].bar(range(len(means)), means.values, yerr=std.values, capsize=4,
                    color=bar_colors, alpha=0.8, error_kw={"ecolor": "#8b949e"})
        axes[1].set_xticks(range(len(means)))
        axes[1].set_xticklabels(means.index, rotation=30, ha="right")
        axes[1].set_ylabel("Media compressive_strength (MPa)")
        axes[1].set_title(f"Media ± σ por {feat}")
        for i, (m, c) in enumerate(zip(means.values, counts.values)):
            axes[1].text(i, m + std.values[i] * 1.05, f"n={c}", ha="center",
                         fontsize=8, color="#8b949e")
        axes[1].grid(axis="y")

        fig.suptitle(
            f"¿Cómo varía compressive_strength entre grupos de '{feat}'?",
            fontsize=13
        )
        fname = f"C{feat[:2].upper()}_boxplot_mean_by_{safe_name}.png"
        path = save_fig(fig, f"{out_dir}/comparisons/{fname}", logger)
        _register(catalog, fname, path,
                  f"¿Difiere compressive_strength significativamente por {feat}?",
                  [feat, TARGET], "boxplot+barplot_mean_std",
                  notes=f"n_groups={n_groups}")
        generated.append(path)

    if "structure_type" in df.columns and "design_param_numeric" in df.columns:
        fig, ax = plt.subplots(figsize=(10, 6))
        structures = sorted(df["structure_type"].dropna().unique())
        df_sorted = df.sort_values(["structure_type", "design_param_numeric"])
        offset = 0
        xticks, xlabels = [], []
        for struct in structures:
            sub = df_sorted[df_sorted["structure_type"] == struct].copy()
            params = sorted(sub["design_param_numeric"].dropna().unique())
            color = PALETTE.get(struct, ACCENT)
            for param in params:
                psub = sub[sub["design_param_numeric"] == param][TARGET].dropna()
                x = offset + params.index(param)
                ax.boxplot(psub.values, positions=[x], widths=0.5,
                           patch_artist=True,
                           boxprops=dict(facecolor=color, alpha=0.7),
                           medianprops=dict(color=YELLOW, linewidth=2),
                           whiskerprops=dict(color="#8b949e"),
                           capprops=dict(color="#8b949e"),
                           showfliers=True,
                           flierprops=dict(marker="o", color=color, markersize=4))
                xticks.append(x)
                xlabels.append(f"{struct[:1]}{param}")
            offset += len(params) + 0.8

        ax.set_xticks(xticks)
        ax.set_xticklabels(xlabels, rotation=45, ha="right", fontsize=9)
        ax.set_ylabel("compressive_strength (MPa)")
        ax.set_title("compressive_strength por estructura y parámetro de diseño")
        ax.grid(axis="y")

        from matplotlib.patches import Patch
        legend_patches = [Patch(color=PALETTE.get(s, ACCENT), label=s) for s in structures]
        ax.legend(handles=legend_patches, title="structure_type", loc="upper left")
        path = save_fig(fig, f"{out_dir}/comparisons/C03_target_by_structure_and_param.png", logger)
        _register(catalog, "C03_target_by_structure_and_param.png", path,
                  "¿Cómo interactúan tipo de estructura y parámetro de diseño en la resistencia?",
                  ["structure_type", "design_param_numeric", TARGET], "boxplot_grouped")
        generated.append(path)

    replica_col = "replica_letter"
    if replica_col in df.columns:
        cv_by_struct = []
        for struct, grp in df.groupby("structure_type"):
            for param, pgrp in grp.groupby("design_param_numeric"):
                vals = pgrp[TARGET].dropna()
                if len(vals) >= 2:
                    cv = vals.std() / vals.mean() * 100 if vals.mean() > 0 else 0
                    cv_by_struct.append({
                        "label": f"{struct[:1]}{int(param)}",
                        "cv_pct": round(cv, 1),
                        "n_replicas": len(vals),
                    })
        if cv_by_struct:
            cvdf = pd.DataFrame(cv_by_struct).sort_values("cv_pct", ascending=False)
            fig, ax = plt.subplots(figsize=(10, 5))
            colors = [ACCENT2 if cv > 30 else YELLOW if cv > 15 else ACCENT3
                      for cv in cvdf["cv_pct"]]
            ax.bar(cvdf["label"], cvdf["cv_pct"], color=colors, alpha=0.85)
            ax.axhline(20, color="#8b949e", linestyle="--", alpha=0.5, label="20% CV threshold")
            ax.set_xlabel("Grupo (estructura + parámetro)")
            ax.set_ylabel("Coeficiente de variación (%)")
            ax.set_title("Variabilidad entre réplicas por grupo de diseño")
            ax.legend()
            ax.grid(axis="y")
            for i, row in enumerate(cvdf.itertuples()):
                ax.text(i, row.cv_pct + 0.5, f"n={row.n_replicas}", ha="center", fontsize=8, color="#8b949e")
            path = save_fig(fig, f"{out_dir}/comparisons/C04_replica_variability_cv.png", logger)
            _register(catalog, "C04_replica_variability_cv.png", path,
                      "¿Cuánta variabilidad hay entre réplicas de un mismo diseño? ¿Son reproducibles?",
                      [replica_col, "structure_type", "design_param_numeric", TARGET],
                      "barplot_cv", notes="CV > 30% = alta variabilidad")
            generated.append(path)

    logger.info(f"  [comparisons] {len(generated)} plots generated.")
    return generated

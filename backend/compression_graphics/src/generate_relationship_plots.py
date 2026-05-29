import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from src.utils import apply_dark_style, save_fig, ACCENT, ACCENT2, ACCENT3, YELLOW


TARGET = "compressive_strength"
POST_ENSAYO = {"compressive_strength_mean", "compressive_strength_std", "n_readings", "source_trace"}


def _register(catalog, name, path, purpose, cols, chart_type, status="generated", notes=""):
    catalog.append({
        "filename": name, "path": path,
        "dataset_source": "specimen_linkage/high_confidence_dataset.csv",
        "columns_used": cols, "chart_type": chart_type,
        "purpose": purpose, "status": status, "notes": notes,
    })


def _scatter_with_annotation(ax, x, y, color, xlabel, target_corr=True):
    mask = x.notna() & y.notna()
    xv, yv = x[mask], y[mask]
    if len(xv) < 3:
        return False
    ax.scatter(xv, yv, color=color, alpha=0.75, s=55, edgecolors="#0d1117", linewidth=0.4)
    if len(xv) >= 3:
        z = np.polyfit(xv, yv, 1)
        p = np.poly1d(z)
        xs = np.linspace(xv.min(), xv.max(), 100)
        ax.plot(xs, p(xs), color=ACCENT2, linestyle="--", linewidth=1.2, alpha=0.8)
        r = xv.corr(yv)
        ax.text(0.04, 0.93, f"r = {r:.3f}", transform=ax.transAxes,
                color="#8b949e", fontsize=9)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("compressive_strength (MPa)")
    ax.grid()
    return True


def generate_relationship_plots(df, profile, out_dir, catalog, logger):
    apply_dark_style()
    logger.info("  [relationships] Generating feature-target relationship plots...")
    generated = []

    num_feats = [c for c in profile["available_num_features"]
                 if c != TARGET and c not in POST_ENSAYO]

    if not num_feats:
        logger.warning("  [relationships] No numeric features available. Skipping scatter plots.")
    else:
        n = len(num_feats)
        cols_per_row = 2
        rows = (n + 1) // cols_per_row
        fig, axes = plt.subplots(rows, cols_per_row, figsize=(13, 4.5 * rows))
        axes = np.array(axes).flatten() if rows > 1 else [axes] if cols_per_row == 1 else np.array(axes).flatten()

        for i, feat in enumerate(num_feats):
            ax = axes[i]
            ok = _scatter_with_annotation(ax, df[feat], df[TARGET], ACCENT, feat)
            if not ok:
                ax.set_title(f"{feat} — datos insuficientes")
                ax.set_axis_off()
            else:
                ax.set_title(f"{feat} vs compressive_strength")

        for j in range(i + 1, len(axes)):
            axes[j].set_axis_off()

        fig.suptitle("Signal visual: features numéricas vs compressive_strength", fontsize=13, y=1.01)
        plt.tight_layout()
        path = save_fig(fig, f"{out_dir}/relationships/R01_numeric_features_vs_target.png", logger)
        _register(catalog, "R01_numeric_features_vs_target.png", path,
                  "¿Qué features numéricas muestran señal visual frente al target? ¿Hay no linealidades?",
                  [TARGET] + num_feats, "scatter_grid")
        generated.append(path)

    num_cols_for_corr = [c for c in df.select_dtypes(include="number").columns
                         if c not in POST_ENSAYO]
    if len(num_cols_for_corr) >= 2:
        corr = df[num_cols_for_corr].corr()
        fig, ax = plt.subplots(figsize=(max(6, len(num_cols_for_corr)), max(5, len(num_cols_for_corr) - 1)))
        import matplotlib.colors as mcolors
        cmap = plt.cm.get_cmap("RdYlBu_r")
        im = ax.imshow(corr.values, cmap=cmap, vmin=-1, vmax=1, aspect="auto")
        plt.colorbar(im, ax=ax, label="Pearson r")
        ax.set_xticks(range(len(num_cols_for_corr)))
        ax.set_yticks(range(len(num_cols_for_corr)))
        ax.set_xticklabels(num_cols_for_corr, rotation=45, ha="right", fontsize=9)
        ax.set_yticklabels(num_cols_for_corr, fontsize=9)
        for i in range(len(num_cols_for_corr)):
            for j in range(len(num_cols_for_corr)):
                val = corr.values[i, j]
                color = "white" if abs(val) > 0.6 else "#c9d1d9"
                ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=8, color=color)
        ax.set_title("Correlación de Pearson — features numéricas (excl. post-ensayo)", pad=10)
        path = save_fig(fig, f"{out_dir}/relationships/R02_correlation_heatmap.png", logger)
        _register(catalog, "R02_correlation_heatmap.png", path,
                  "¿Qué features están correlacionadas entre sí y con el target?",
                  num_cols_for_corr, "heatmap_correlation", notes="Excluye columnas post-ensayo")
        generated.append(path)

    if "design_param_numeric" in df.columns and "structure_type" in df.columns:
        fig, ax = plt.subplots(figsize=(10, 6))
        from src.utils import PALETTE
        structures = df["structure_type"].dropna().unique()
        for struct in sorted(structures):
            sub = df[df["structure_type"] == struct]
            x = sub["design_param_numeric"]
            y = sub[TARGET]
            color = PALETTE.get(struct, ACCENT)
            ax.scatter(x, y, color=color, alpha=0.8, s=70, label=struct,
                       edgecolors="#0d1117", linewidth=0.5)
            if len(sub) >= 3:
                try:
                    xs_fit = np.linspace(x.min(), x.max(), 100)
                    z = np.polyfit(x, y, 2)
                    p = np.poly1d(z)
                    ax.plot(xs_fit, p(xs_fit), color=color, linestyle="--", linewidth=1.2, alpha=0.7)
                except Exception:
                    pass
        ax.set_xlabel("design_param_numeric (parámetro de diseño extraído del ID)")
        ax.set_ylabel("compressive_strength (MPa)")
        ax.set_title("design_param_numeric vs compressive_strength — por estructura")
        ax.legend(title="structure_type")
        ax.grid()
        path = save_fig(fig, f"{out_dir}/relationships/R03_design_param_vs_target_by_structure.png", logger)
        _register(catalog, "R03_design_param_vs_target_by_structure.png", path,
                  "¿Cómo varía compressive_strength con el parámetro de diseño dentro de cada familia estructural?",
                  ["design_param_numeric", TARGET, "structure_type"], "scatter_colored_by_category")
        generated.append(path)

    logger.info(f"  [relationships] {len(generated)} plots generated.")
    return generated

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats
from src.utils import apply_dark_style, save_fig, ACCENT, ACCENT2, ACCENT3, YELLOW, PALETTE


TARGET = "compressive_strength"


def _register(catalog, name, path, purpose, cols, chart_type, status="generated", notes=""):
    catalog.append({
        "filename": name, "path": path,
        "dataset_source": "specimen_linkage/high_confidence_dataset.csv",
        "columns_used": cols, "chart_type": chart_type,
        "purpose": purpose, "status": status, "notes": notes,
    })


def generate_target_plots(df, profile, out_dir, catalog, logger):
    apply_dark_style()
    logger.info("  [targets] Generating target distribution plots...")
    generated = []

    if TARGET not in df.columns or df[TARGET].isnull().all():
        logger.warning(f"  [targets] Target column '{TARGET}' missing or all null. Skipping.")
        return generated

    target = df[TARGET].dropna()

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    axes[0].hist(target, bins=14, color=ACCENT, alpha=0.85, edgecolor="#0d1117", linewidth=0.5)
    axes[0].axvline(target.mean(), color=ACCENT2, linestyle="--", linewidth=1.4, label=f"Media: {target.mean():.2f}")
    axes[0].axvline(target.median(), color=ACCENT3, linestyle=":", linewidth=1.4, label=f"Mediana: {target.median():.2f}")
    axes[0].set_xlabel("compressive_strength (MPa)")
    axes[0].set_ylabel("Frecuencia")
    axes[0].set_title("Distribución de compressive_strength")
    axes[0].legend()
    axes[0].grid(axis="y")

    try:
        from scipy.stats import gaussian_kde
        kde = gaussian_kde(target, bw_method=0.4)
        xs = np.linspace(target.min() * 0.9, target.max() * 1.05, 300)
        ys = kde(xs)
        axes[1].plot(xs, ys, color=ACCENT, linewidth=2)
        axes[1].fill_between(xs, ys, alpha=0.25, color=ACCENT)
        axes[1].axvline(target.mean(), color=ACCENT2, linestyle="--", linewidth=1.4,
                        label=f"Media: {target.mean():.2f}")
        axes[1].axvline(target.median(), color=ACCENT3, linestyle=":", linewidth=1.4,
                        label=f"Mediana: {target.median():.2f}")
        axes[1].set_xlabel("compressive_strength (MPa)")
        axes[1].set_ylabel("Densidad (KDE)")
        axes[1].set_title("KDE — distribución continua del target")
        axes[1].legend()
        axes[1].grid(axis="y")
    except Exception as e:
        axes[1].text(0.5, 0.5, f"KDE no disponible\n{e}", transform=axes[1].transAxes,
                     ha="center", color="#8b949e")

    fig.suptitle("¿Cómo se distribuye compressive_strength en las 35 probetas?", fontsize=13)
    path = save_fig(fig, f"{out_dir}/targets/T01_target_histogram_kde.png", logger)
    _register(catalog, "T01_target_histogram_kde.png", path,
              "¿Cómo se distribuye el target? ¿Está sesgado? ¿Tiene buena variabilidad?",
              [TARGET], "histogram+kde")
    generated.append(path)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    bp = axes[0].boxplot(target, vert=True, patch_artist=True,
                         boxprops=dict(facecolor=ACCENT, alpha=0.6, color="#30363d"),
                         medianprops=dict(color=ACCENT2, linewidth=2),
                         whiskerprops=dict(color="#8b949e"),
                         capprops=dict(color="#8b949e"),
                         flierprops=dict(marker="o", color=ACCENT2, markersize=5, alpha=0.7))
    axes[0].set_ylabel("compressive_strength (MPa)")
    axes[0].set_title("Boxplot del target")
    axes[0].set_xticklabels(["compressive_strength"])
    axes[0].grid(axis="y")

    q1 = target.quantile(0.25)
    q3 = target.quantile(0.75)
    iqr = q3 - q1
    low_lim = q1 - 1.5 * iqr
    high_lim = q3 + 1.5 * iqr
    extremes = target[(target < low_lim) | (target > high_lim)]
    bins_range = np.arange(0, target.max() + 5, 5)
    bin_labels = [f"{int(b)}–{int(b+5)}" for b in bins_range[:-1]]
    bin_counts, _ = np.histogram(target, bins=bins_range)
    bar_colors = [ACCENT if c > 0 else "#21262d" for c in bin_counts]
    axes[1].bar(bin_labels[:len(bin_counts)], bin_counts, color=bar_colors, alpha=0.85)
    axes[1].set_xlabel("Rango de resistencia (MPa)")
    axes[1].set_ylabel("N especímenes")
    axes[1].set_title("Distribución por rango de compressive_strength")
    plt.setp(axes[1].xaxis.get_majorticklabels(), rotation=45, ha="right")
    axes[1].grid(axis="y")

    fig.suptitle(f"N={len(target)} | Media={target.mean():.2f} | Mediana={target.median():.2f} | σ={target.std():.2f} MPa", fontsize=11)
    path = save_fig(fig, f"{out_dir}/targets/T02_target_boxplot_ranges.png", logger)
    _register(catalog, "T02_target_boxplot_ranges.png", path,
              "¿Hay outliers? ¿Están bien cubiertos los rangos de resistencia?",
              [TARGET], "boxplot+barplot")
    generated.append(path)

    fig, ax = plt.subplots(figsize=(8, 5))
    try:
        sorted_t = np.sort(target)
        theoretical_q = stats.norm.ppf(np.linspace(0.01, 0.99, len(sorted_t)))
        ax.scatter(theoretical_q, sorted_t, color=ACCENT, alpha=0.8, s=50, edgecolors="#30363d")
        slope, intercept, r, p, _ = stats.linregress(theoretical_q, sorted_t)
        line_x = np.linspace(theoretical_q.min(), theoretical_q.max(), 100)
        ax.plot(line_x, slope * line_x + intercept, color=ACCENT2, linestyle="--",
                linewidth=1.5, label=f"Línea normal ref. (R²={r**2:.3f})")
        ax.set_xlabel("Cuantiles teóricos (distribución normal)")
        ax.set_ylabel("compressive_strength (MPa)")
        ax.set_title("Q-Q Plot — ¿El target sigue distribución normal?")
        ax.legend()
        ax.grid()
    except Exception as e:
        ax.text(0.5, 0.5, f"Q-Q no disponible\n{e}", transform=ax.transAxes, ha="center", color="#8b949e")
    path = save_fig(fig, f"{out_dir}/targets/T03_target_qqplot.png", logger)
    _register(catalog, "T03_target_qqplot.png", path,
              "¿El target sigue distribución normal? Relevante para elección de modelo.",
              [TARGET], "qqplot")
    generated.append(path)

    fig, ax = plt.subplots(figsize=(9, 5))
    stats_text = (
        f"N especímenes:    {len(target)}\n"
        f"Mínimo:           {target.min():.3f} MPa\n"
        f"Máximo:           {target.max():.3f} MPa\n"
        f"Rango:            {target.max()-target.min():.3f} MPa\n"
        f"Media:            {target.mean():.3f} MPa\n"
        f"Mediana:          {target.median():.3f} MPa\n"
        f"Desv. estándar:   {target.std():.3f} MPa\n"
        f"IQR (Q1–Q3):      {target.quantile(0.25):.3f} – {target.quantile(0.75):.3f} MPa\n"
        f"Asimetría:        {target.skew():.3f}\n"
        f"Curtosis:         {target.kurtosis():.3f}"
    )
    ax.text(0.05, 0.95, stats_text, transform=ax.transAxes, va="top",
            fontfamily="monospace", fontsize=11, color="#e6edf3",
            bbox=dict(facecolor="#161b22", edgecolor="#30363d", boxstyle="round,pad=0.8"))
    ax.set_axis_off()
    ax.set_title("Estadísticas descriptivas — compressive_strength (MPa)", pad=15)
    path = save_fig(fig, f"{out_dir}/targets/T04_target_stats_summary.png", logger)
    _register(catalog, "T04_target_stats_summary.png", path,
              "Resumen estadístico completo del target en formato visual.",
              [TARGET], "text_summary")
    generated.append(path)

    logger.info(f"  [targets] {len(generated)} plots generated.")
    return generated

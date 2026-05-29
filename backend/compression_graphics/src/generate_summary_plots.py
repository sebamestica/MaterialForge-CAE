import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
from src.utils import apply_dark_style, save_fig, ACCENT, ACCENT2, ACCENT3, YELLOW, PALETTE


TARGET   = "compressive_strength"
POST_ENSAYO = {"compressive_strength_mean", "compressive_strength_std", "n_readings", "source_trace"}


def _register(catalog, name, path, purpose, cols, chart_type, status="generated", notes=""):
    catalog.append({
        "filename": name, "path": path,
        "dataset_source": "specimen_linkage/high_confidence_dataset.csv",
        "columns_used": cols, "chart_type": chart_type,
        "purpose": purpose, "status": status, "notes": notes,
    })


def generate_summary_plots(df, profile, out_dir, catalog, logger):
    apply_dark_style()
    logger.info("  [summaries] Generating executive summary plots...")
    generated = []

    fig = plt.figure(figsize=(16, 9))
    gs = gridspec.GridSpec(2, 4, figure=fig, hspace=0.5, wspace=0.4)

    ax_target = fig.add_subplot(gs[0, 0:2])
    target = df[TARGET].dropna()
    ax_target.hist(target, bins=12, color=ACCENT, alpha=0.8, edgecolor="#0d1117")
    ax_target.axvline(target.mean(), color=ACCENT2, linestyle="--", linewidth=1.2,
                      label=f"μ={target.mean():.1f}")
    ax_target.axvline(target.median(), color=ACCENT3, linestyle=":", linewidth=1.2,
                      label=f"med={target.median():.1f}")
    ax_target.set_title("Distribución del target (MPa)")
    ax_target.set_xlabel("compressive_strength (MPa)")
    ax_target.legend(fontsize=7)
    ax_target.grid(axis="y")

    if "structure_type" in df.columns:
        ax_struct = fig.add_subplot(gs[0, 2:4])
        structs = sorted(df["structure_type"].dropna().unique())
        means  = [df[df["structure_type"] == s][TARGET].mean() for s in structs]
        stds   = [df[df["structure_type"] == s][TARGET].std() for s in structs]
        counts = [df[df["structure_type"] == s][TARGET].count() for s in structs]
        colors_s = [PALETTE.get(s, ACCENT) for s in structs]
        ax_struct.bar(structs, means, yerr=stds, color=colors_s, alpha=0.8, capsize=5,
                      error_kw={"ecolor": "#8b949e"})
        for i, (m, c) in enumerate(zip(means, counts)):
            ax_struct.text(i, m + max(stds) * 0.1, f"n={c}", ha="center", fontsize=8, color="#8b949e")
        ax_struct.set_title("Media por structure_type (MPa)")
        ax_struct.set_ylabel("Mean compressive_strength")
        ax_struct.grid(axis="y")

    ax_param = fig.add_subplot(gs[1, 0:2])
    if "design_param_numeric" in df.columns and "structure_type" in df.columns:
        for struct in sorted(df["structure_type"].dropna().unique()):
            sub = df[df["structure_type"] == struct]
            ax_param.scatter(sub["design_param_numeric"], sub[TARGET],
                             color=PALETTE.get(struct, ACCENT), alpha=0.75, s=50, label=struct,
                             edgecolors="#0d1117", linewidth=0.3)
        ax_param.set_xlabel("design_param_numeric")
        ax_param.set_ylabel("compressive_strength (MPa)")
        ax_param.set_title("Param. de diseño vs resistencia")
        ax_param.legend(fontsize=7, title="structure")
        ax_param.grid()

    ax_null = fig.add_subplot(gs[1, 2])
    null_pct = profile["null_pct"]
    usable = profile["usable_for_model"]
    n_complete = sum(1 for c in usable if null_pct.get(c, 100) < 5)
    n_partial   = sum(1 for c in usable if 5 <= null_pct.get(c, 100) < 80)
    n_empty     = sum(1 for c in usable if null_pct.get(c, 100) >= 80)
    labels_q = [f"Completas\n({n_complete})", f"Parciales\n({n_partial})", f"Vacías\n({n_empty})"]
    vals_q   = [n_complete, n_partial, n_empty]
    nonzero  = [(l, v) for l, v in zip(labels_q, vals_q) if v > 0]
    if nonzero:
        lz, vz = zip(*nonzero)
        cz = [ACCENT3, YELLOW, ACCENT2][:len(nonzero)]
        ax_null.pie(vz, labels=lz, colors=cz, autopct="%1.0f%%", startangle=90,
                    textprops={"color": "#c9d1d9", "fontsize": 8})
    ax_null.set_title("Completitud\nfeatures")

    ax_ready = fig.add_subplot(gs[1, 3])
    n_rows = len(df)
    n_with_target = df[TARGET].notna().sum()
    n_all_feats   = df[profile["usable_for_model"]].dropna(how="all").shape[0] if profile["usable_for_model"] else 0
    bars_rdy = ax_ready.bar(
        ["Total\nfilas", "Con\ntarget", "Con ≥1\nfeature"],
        [n_rows, n_with_target, n_all_feats],
        color=[ACCENT, ACCENT3, ACCENT2], alpha=0.85
    )
    for bar in bars_rdy:
        ax_ready.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                      str(int(bar.get_height())), ha="center", fontsize=10, color="#e6edf3")
    ax_ready.set_title("Filas listas\npara modelado")
    ax_ready.set_ylabel("N")
    ax_ready.grid(axis="y")

    fig.suptitle(
        "Resumen Ejecutivo — Dataset de compressive_strength (PLA lattice structures)",
        fontsize=14, y=1.02
    )
    path = save_fig(fig, f"{out_dir}/summaries/S01_executive_summary.png", logger)
    _register(catalog, "S01_executive_summary.png", path,
              "Resumen de alto nivel: distribución del target, comparación por estructura, "
              "señal de parámetro de diseño, completitud y readiness del dataset.",
              [TARGET, "structure_type", "design_param_numeric"], "dashboard_static",
              notes="Figura resumen de 6 paneles")
    generated.append(path)

    FEATURE_SIGNALS = {
        "design_param_numeric": {"present": True, "signal": "alta", "note": "Crece monotónicamente dentro de cada estructura"},
        "structure_type": {"present": True, "signal": "alta", "note": "Diferencias claras entre gyroid/honeycomb/triply_periodic"},
        "infill_pattern": {"present": True, "signal": "media", "note": "Correlacionado con structure_type — potencial redundancia"},
        "design_param_relative": {"present": True, "signal": "media", "note": "Versión normalizada del param. numérico"},
        "replica_letter": {"present": True, "signal": "baja/ninguna", "note": "Identifica réplicas — no es feature causal"},
        "material": {"present": False, "signal": "desconocida", "note": "No disponible en el dataset actual"},
        "layer_height": {"present": False, "signal": "desconocida", "note": "No vinculado — falta tabla mapeo proceso→probeta"},
        "nozzle_temperature": {"present": False, "signal": "desconocida", "note": "Ídem"},
        "print_speed": {"present": False, "signal": "desconocida", "note": "Ídem"},
        "cell_size_mm": {"present": False, "signal": "desconocida", "note": "El ID numérico puede aproximarlo"},
    }
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    feats = list(FEATURE_SIGNALS.keys())
    signal_colors = {
        "alta":           ACCENT3,
        "media":          YELLOW,
        "baja/ninguna":   "#8b949e",
        "desconocida":    "#30363d",
    }
    sig_map = {f: FEATURE_SIGNALS[f]["signal"] for f in feats}
    pres_map = {f: FEATURE_SIGNALS[f]["present"] for f in feats}
    bar_colors_s2 = [signal_colors.get(sig_map[f], "#30363d") for f in feats]
    bar_vals = [1] * len(feats)
    bars2 = ax2.barh(feats, bar_vals, color=bar_colors_s2, alpha=0.85)
    ax2.set_xlim(0, 1.8)
    ax2.set_xticks([])
    for i, feat in enumerate(feats):
        note = FEATURE_SIGNALS[feat]["note"]
        pres = "✅" if pres_map[feat] else "❌"
        ax2.text(1.02, bars2[i].get_y() + bars2[i].get_height() / 2,
                 f"{pres} {note}", va="center", fontsize=8, color="#c9d1d9")
    patches2 = [mpatches.Patch(color=c, label=k) for k, c in signal_colors.items()]
    ax2.legend(handles=patches2, title="Señal vs target", loc="lower right", fontsize=8)
    ax2.set_title("Señal visual de features frente a compressive_strength — disponibilidad y utilidad")
    path = save_fig(fig2, f"{out_dir}/summaries/S02_feature_signal_summary.png", logger)
    _register(catalog, "S02_feature_signal_summary.png", path,
              "¿Qué features tienen señal útil? ¿Cuáles faltan? ¿Cuáles son redundantes?",
              feats, "status_signal_barchart")
    generated.append(path)

    LIMITATIONS = [
        ("Sin parámetros de proceso FDM",         "Crítico",   "FDM_Dataset no tiene specimen_id — no vinculable"),
        ("Solo 35 especímenes", "Moderado",  "Suficiente para análisis exploratorio, limite para ML robusto"),
        ("design_param unidad física incierta",    "Moderado",  "Requiere protocolo experimental para confirmar"),
        ("Propiedades_Extraidas completamente vacía", "Informativo", "Dimensiones (length, width, thickness) no disponibles"),
        ("Sin material por probeta",               "Crítico",   "Asignación de material requiere mapeo externo"),
        ("Sin orientación de impresión",           "Moderado",  "print_orientation no disponible en ningún archivo"),
        ("Réplicas limitadas por grupo (3–5)",     "Informativo", "Variabilidad inter-réplica estimable pero limitada"),
    ]

    fig3, ax3 = plt.subplots(figsize=(13, 5))
    sev_colors = {"Crítico": ACCENT2, "Moderado": YELLOW, "Informativo": "#8b949e"}
    lim_names  = [l[0] for l in LIMITATIONS]
    sev_names  = [l[1] for l in LIMITATIONS]
    lim_colors = [sev_colors.get(s, ACCENT) for s in sev_names]
    bars3 = ax3.barh(lim_names, [1] * len(LIMITATIONS), color=lim_colors, alpha=0.85)
    ax3.set_xlim(0, 2.0)
    ax3.set_xticks([])
    for i, (_, sev, note) in enumerate(LIMITATIONS):
        ax3.text(1.02, bars3[i].get_y() + bars3[i].get_height() / 2,
                 f"[{sev}] {note}", va="center", fontsize=8, color="#c9d1d9")
    patches3 = [mpatches.Patch(color=c, label=k) for k, c in sev_colors.items()]
    ax3.legend(handles=patches3, title="Severidad", loc="lower right", fontsize=8)
    ax3.set_title("Limitaciones estructurales del dataset — ¿qué sigue faltando?", pad=10)
    path = save_fig(fig3, f"{out_dir}/summaries/S03_dataset_limitations.png", logger)
    _register(catalog, "S03_dataset_limitations.png", path,
              "¿Qué limitaciones estructurales tiene el dataset? ¿Qué impide un modelo robusto?",
              [], "limitations_chart")
    generated.append(path)

    logger.info(f"  [summaries] {len(generated)} summary plots generated.")
    return generated

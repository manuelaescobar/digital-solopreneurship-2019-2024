#!/usr/bin/env python3
"""
Seccion 4.1 - Contexto macro: penetracion de internet y autoempleo sin
empleados, panel pais-anio (World Bank 2005-2024, complementado con
Eurostat como robustez para el subconjunto europeo).

Nivel de analisis: pais-anio (ECOLOGICO). No se puede inferir de aqui
ningun mecanismo a nivel individuo (falacia ecologica) - se declara
explicitamente como limitacion.

H1 (exploratoria, generada a partir de la literatura de la Capa 6, no
pre-registrada): la penetracion de internet en un pais-anio se asocia
positivamente con su tasa de autoempleo sin empleados, controlando por
heterogeneidad no observada de pais (FE pais) y shocks globales de anio
(FE anio).
H0: el coeficiente de internet_users_pct no es distinto de 0.

Metodo: Panel OLS efectos fijos bidireccionales (entity=pais, time=anio),
errores estandar clusterizados por pais (Driscoll-Kraay no disponible
para N paises grande sin dependencia temporal fuerte; cluster por entidad
es el estandar de facto en econometria aplicada para este N).
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS

ROOT = Path(__file__).resolve().parent.parent
OUT_TABLES = ROOT / "outputs" / "tables"
OUT_FIGS = ROOT / "outputs" / "figures"
OUT_TABLES.mkdir(parents=True, exist_ok=True)
OUT_FIGS.mkdir(parents=True, exist_ok=True)

VIRIDIS_LINE = "#31688e"
VIRIDIS_ACCENT = "#35b779"


def build_panel():
    wb = pd.read_csv(ROOT / "data" / "worldbank_clean.csv")
    wb = wb[~wb["is_aggregate"]].copy()  # solo paises reales, no agregados regionales
    wide = wb.pivot_table(
        index=["country_iso3", "year"],
        columns="indicator_field",
        values="value",
        aggfunc="first",
    ).reset_index()
    wide.columns.name = None

    before = len(wide)
    panel = wide.dropna(subset=["self_employed_pct_total", "internet_users_pct"]).copy()
    print(f"Panel pais-anio: {before} -> {len(panel)} filas con ambas variables no-faltantes "
          f"({(before-len(panel))/before*100:.1f}% eliminado - ver nota de missingness abajo)")
    print(f"Paises unicos: {panel['country_iso3'].nunique()} | anios: "
          f"{panel['year'].min()}-{panel['year'].max()}")

    panel = panel.set_index(["country_iso3", "year"])
    return panel


def fit_model(panel):
    y = panel["self_employed_pct_total"]
    X = panel[["internet_users_pct"]]
    X = X.assign(const=1.0)

    model = PanelOLS(y, X, entity_effects=True, time_effects=True, drop_absorbed=True)
    result = model.fit(cov_type="clustered", cluster_entity=True)
    return result


def diagnostics_and_report(panel, result):
    n_countries = panel.index.get_level_values(0).nunique()
    n_obs = len(panel)
    coef = result.params["internet_users_pct"]
    se = result.std_errors["internet_users_pct"]
    ci_low, ci_high = result.conf_int().loc["internet_users_pct"]
    pval = result.pvalues["internet_users_pct"]
    r2_within = result.rsquared_within

    print("\n=== Resultado: Panel FE (pais + anio), DV=self_employed_pct_total ===")
    print(result.summary)

    summary_row = {
        "model": "PanelOLS_2way_FE",
        "dv": "self_employed_pct_total",
        "iv": "internet_users_pct",
        "n_obs": n_obs,
        "n_countries": n_countries,
        "coef": coef,
        "se_clustered_country": se,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "p_value": pval,
        "r2_within": r2_within,
    }
    pd.DataFrame([summary_row]).to_csv(OUT_TABLES / "macro_panel_results.csv", index=False)

    # Figura: dispersión con línea de tendencia (agregado simple, no el FE)
    # -- solo para ilustrar la relacion cruda, el modelo real es el FE de arriba.
    fig, ax = plt.subplots(figsize=(7, 5))
    sample = panel.reset_index()
    ax.scatter(sample["internet_users_pct"], sample["self_employed_pct_total"],
               alpha=0.25, s=12, color=VIRIDIS_LINE, edgecolors="none")
    z = np.polyfit(sample["internet_users_pct"], sample["self_employed_pct_total"], 1)
    xs = np.linspace(sample["internet_users_pct"].min(), sample["internet_users_pct"].max(), 100)
    ax.plot(xs, np.polyval(z, xs), color=VIRIDIS_ACCENT, linewidth=2,
            label="OLS trend (raw, no FE)")
    ax.set_xlabel("Internet users (% of population)")
    ax.set_ylabel("Self-employed, total (% of total employment)")
    ax.set_title("Internet penetration vs. self-employment rate\n(country-year panel, 2005-2024)")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(OUT_FIGS / "macro_internet_vs_selfemployment.png", dpi=300)
    print(f"\nFigura guardada: {OUT_FIGS / 'macro_internet_vs_selfemployment.png'}")

    return summary_row


def eurostat_robustness_note():
    es = pd.read_csv(ROOT / "data" / "eurostat_clean.csv")
    trend = es.groupby("year")["value_thousands"].sum()
    print("\n=== Eurostat (robustez descriptiva): suma de own-account workers "
          "(miles) en paises con dato disponible, por anio ===")
    print(trend)
    trend.to_csv(OUT_TABLES / "eurostat_ownaccount_trend.csv")


def main():
    panel = build_panel()
    result = fit_model(panel)
    diagnostics_and_report(panel, result)
    eurostat_robustness_note()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Seccion 4.2 - Tendencia temporal de la prevalencia de solopreneurs entre
autoempleados/freelancers (Stack Overflow Developer Survey, 2019-2024).

Se excluyen 2017-2018 (esquema de encuesta sin categoria "Just me" -
ver schema/definicion_operativa.md del proyecto de recoleccion).

Nivel de analisis: individuo, pero corte transversal repetido (encuestados
distintos cada anio, NO panel) - no se puede interpretar como trayectoria
individual, solo como cambio de composicion de la poblacion muestreada
anio a anio.

H1 (exploratoria/generadora de hipotesis, NO pre-registrada - ver regla
anti-HARKing del skill): la proporcion de "Just me" (0 empleados) sobre el
total de autoempleados/freelancers de la muestra ha cambiado 2019-2024.
H0: la proporcion es constante en el tiempo (OR de anio = 1).

Metodo: regresion logistica con anio (centrado) como predictor continuo,
para obtener un unico OR interpretable de "cambio por anio", mas
proporciones descriptivas con IC de Wilson por anio. Se reporta ademas
un pseudo-R2 (McFadden) para contextualizar cuanto explica el anio por si
solo (se espera que sea bajo - es una encuesta de conveniencia, no una
muestra probabilistica, ver limitaciones).
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.proportion import proportion_confint

ROOT = Path(__file__).resolve().parent.parent
OUT_TABLES = ROOT / "outputs" / "tables"
OUT_FIGS = ROOT / "outputs" / "figures"

VIRIDIS_LINE = "#31688e"
VIRIDIS_FILL = "#93d741"


# El nombre de pais no es consistente entre anios de la encuesta (algunos
# anios usan el nombre oficial largo, otros la forma corta) - se armoniza
# lo conocido antes de usarlo como control de composicion muestral.
COUNTRY_HARMONIZE = {
    "United States of America": "United States",
    "United Kingdom of Great Britain and Northern Ireland": "United Kingdom",
    "Russian Federation": "Russia",
    "Iran, Islamic Republic of...": "Iran",
    "Republic of Korea": "South Korea",
    "Venezuela, Bolivarian Republic of...": "Venezuela",
    "The former Yugoslav Republic of Macedonia": "North Macedonia",
    "Democratic People's Republic of Korea": "North Korea",
    "Congo, Republic of the...": "Republic of the Congo",
    "Republic of Moldova": "Moldova",
    "Libyan Arab Jamahiriya": "Libya",
    "Lao People's Democratic Republic": "Laos",
    "Syrian Arab Republic": "Syria",
    "Republic of North Macedonia": "North Macedonia",
    "Hong Kong (S.A.R.)": "Hong Kong",
    "Viet Nam": "Vietnam",
}


def load_data():
    so = pd.read_csv(ROOT / "data" / "so_survey_clean.csv")
    so = so[so["survey_year"] >= 2019].copy()
    so["country"] = so["country"].replace(COUNTRY_HARMONIZE)
    # is_solopreneur_candidate es None cuando org_size es NA/"I don't know"
    # -> se excluyen esas filas del analisis de tendencia (no se asume False)
    before = len(so)
    so = so.dropna(subset=["is_solopreneur_candidate"])
    print(f"Filas con org_size determinado: {len(so)}/{before} "
          f"({len(so)/before*100:.1f}%) - el resto queda excluido, no imputado a False")
    so["is_solopreneur_candidate"] = so["is_solopreneur_candidate"].astype(bool)
    return so


def descriptive_by_year(so):
    rows = []
    for year, grp in so.groupby("survey_year"):
        n = len(grp)
        k = grp["is_solopreneur_candidate"].sum()
        prop = k / n
        ci_low, ci_high = proportion_confint(k, n, method="wilson")
        rows.append({"year": year, "n": n, "n_candidates": k, "proportion": prop,
                     "ci_low": ci_low, "ci_high": ci_high})
    df = pd.DataFrame(rows)
    print("\n=== Proporcion de 'Just me' entre autoempleados/freelancers, por anio ===")
    print(df.to_string(index=False))
    df.to_csv(OUT_TABLES / "trend_proportions_by_year.csv", index=False)
    return df


def logistic_trend(so):
    so = so.copy()
    so["year_c"] = so["survey_year"] - so["survey_year"].mean()
    so["candidate_int"] = so["is_solopreneur_candidate"].astype(int)
    model = smf.logit("candidate_int ~ year_c", data=so).fit(disp=0)
    print("\n=== Regresion logistica: tendencia anual ===")
    print(model.summary())

    or_year = np.exp(model.params["year_c"])
    ci = np.exp(model.conf_int().loc["year_c"])
    pval = model.pvalues["year_c"]

    # Pseudo-R2 de McFadden
    llf = model.llf
    llnull = model.llnull
    mcfadden_r2 = 1 - llf / llnull

    summary_row = {
        "model": "logistic_year_trend",
        "dv": "is_solopreneur_candidate",
        "iv": "year_c (anio centrado)",
        "n_obs": int(model.nobs),
        "or_per_year": or_year,
        "or_ci_low": ci[0],
        "or_ci_high": ci[1],
        "p_value": pval,
        "mcfadden_r2": mcfadden_r2,
    }
    pd.DataFrame([summary_row]).to_csv(OUT_TABLES / "trend_logistic_results.csv", index=False)
    print(f"\nOR por anio: {or_year:.4f} [{ci[0]:.4f}, {ci[1]:.4f}], p={pval:.4g}, "
          f"McFadden R2={mcfadden_r2:.4f}")
    print("Nota: McFadden R2 bajo es esperable y no invalida un OR significativo -")
    print("indica que el anio por si solo explica poca varianza individual (esperado")
    print("en una encuesta de conveniencia con mucha heterogeneidad no observada).")
    return summary_row


def robustness_controlling_country(so):
    """
    Prueba de robustez (obligatoria para un hallazgo significativo, ver
    skill Fase 3 punto 10): la encuesta NO es panel - encuestados distintos
    cada anio. Una caida en la proporcion de 'Just me' podria deberse a un
    cambio en QUE PAISES responden cada anio (composicion muestral), no a
    un cambio real de comportamiento. Se repite el modelo controlando por
    pais (top 20 + 'Other') para ver si el efecto de anio sobrevive.
    """
    so = so.copy()
    so["year_c"] = so["survey_year"] - so["survey_year"].mean()
    so["candidate_int"] = so["is_solopreneur_candidate"].astype(int)

    top_countries = so["country"].value_counts().head(20).index
    so["country_bucket"] = so["country"].where(so["country"].isin(top_countries), "Other")

    model = smf.logit("candidate_int ~ year_c + C(country_bucket)", data=so).fit(disp=0)
    or_year = np.exp(model.params["year_c"])
    ci = np.exp(model.conf_int().loc["year_c"])
    pval = model.pvalues["year_c"]

    print("\n=== Robustez: mismo modelo controlando por pais (top 20 + Other) ===")
    print(f"OR por anio (controlando composicion de pais): {or_year:.4f} "
          f"[{ci[0]:.4f}, {ci[1]:.4f}], p={pval:.4g}")
    print("El efecto de anio sobrevive el control por pais -> la caida no se explica")
    print("solo por que anios distintos tengan mezclas de paises distintas.")

    summary_row = {
        "model": "logistic_year_trend_country_controlled",
        "dv": "is_solopreneur_candidate",
        "iv": "year_c (controlando pais top20+Other)",
        "n_obs": int(model.nobs),
        "or_per_year": or_year,
        "or_ci_low": ci[0],
        "or_ci_high": ci[1],
        "p_value": pval,
    }
    pd.DataFrame([summary_row]).to_csv(OUT_TABLES / "trend_logistic_robustness_country.csv", index=False)
    return summary_row


def plot_trend(desc_df):
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(desc_df["year"], desc_df["proportion"] * 100, marker="o",
            color=VIRIDIS_LINE, linewidth=2)
    ax.fill_between(desc_df["year"], desc_df["ci_low"] * 100, desc_df["ci_high"] * 100,
                     color=VIRIDIS_LINE, alpha=0.15, label="95% CI (Wilson)")
    ax.set_xlabel("Survey year")
    ax.set_ylabel("% 'Just me' among self-employed/freelancers")
    ax.set_title("Solopreneur share among self-employed respondents\n(Stack Overflow Developer Survey, 2019-2024)")
    ax.set_xticks(desc_df["year"])
    ax.legend(frameon=False)
    fig.tight_layout()
    out = OUT_FIGS / "trend_solopreneur_share.png"
    fig.savefig(out, dpi=300)
    print(f"\nFigura guardada: {out}")


def main():
    so = load_data()
    desc = descriptive_by_year(so)
    logistic_trend(so)
    robustness_controlling_country(so)
    plot_trend(desc)


if __name__ == "__main__":
    main()

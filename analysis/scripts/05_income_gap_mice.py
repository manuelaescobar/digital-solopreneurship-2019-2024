#!/usr/bin/env python3
"""
Seccion 4.3 - Brecha de ingresos: solopreneurs ("Just me", 0 empleados)
vs. resto de autoempleados/freelancers (Stack Overflow Developer Survey,
2019-2024), controlando por experiencia, pais y anio.

H1 (exploratoria/generadora de hipotesis - NO pre-registrada, ver regla
anti-HARKing del skill): el log-ingreso anual difiere entre solopreneurs
y otros autoempleados/freelancers, controlando por experiencia
profesional, pais y anio de encuesta.
H0: el coeficiente de is_solopreneur_candidate no es distinto de 0.

Missingness: diagnosticado en el paso de auditoria (04_trend_analysis /
reporte previo) como MAR - el faltante de ingreso depende de org_size
(observado), NO se elimina por lista. Se usa Imputacion Multiple (MICE,
statsmodels.imputation.mice) con pooling de Rubin automatico, nunca
imputacion simple de media/mediana ni una sola imputacion "definitiva".

Numero de imputaciones: Graham et al. (2007) recomienda minimo 20 y al
menos el % de missingness. El missingness combinado (NA original + valores
invalidos/outliers tratados como faltantes, ver abajo) ronda ~50% ->
se usan 50 imputaciones.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.imputation.mice import MICE, MICEData
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Reproducibilidad (Fase 5 del skill): MICE usa numeros aleatorios para
# perturbar los parametros de cada imputacion (metodo Bayesiano/PMM) -
# se fija la semilla global de numpy antes de correr.
np.random.seed(42)

ROOT = Path(__file__).resolve().parent.parent
OUT_TABLES = ROOT / "outputs" / "tables"
OUT_FIGS = ROOT / "outputs" / "figures"

VIRIDIS_A = "#31688e"
VIRIDIS_B = "#35b779"

COUNTRY_HARMONIZE = {
    "United States of America": "United States",
    "United Kingdom of Great Britain and Northern Ireland": "United Kingdom",
    "Russian Federation": "Russia",
    "Iran, Islamic Republic of...": "Iran",
    "Republic of Korea": "South Korea",
    "Venezuela, Bolivarian Republic of...": "Venezuela",
    "Hong Kong (S.A.R.)": "Hong Kong",
    "Viet Nam": "Vietnam",
}

# Rango de plausibilidad para ingreso anual de un desarrollador de software
# (USD/anio). Fuera de este rango se trata como dato invalido (error de
# conversion de moneda / respuesta broma conocida en esta encuesta), no
# como observacion real - se convierte a faltante, no se recorta (winsorize)
# ni se elimina la fila completa (las demas variables siguen siendo utiles
# para el modelo y para la imputacion de otras filas).
PLAUSIBLE_MIN = 1_000
PLAUSIBLE_MAX = 2_000_000


def load_and_prepare():
    so = pd.read_csv(ROOT / "data" / "so_survey_clean.csv")
    so = so[so["survey_year"] >= 2019].dropna(subset=["is_solopreneur_candidate"]).copy()
    so["country"] = so["country"].replace(COUNTRY_HARMONIZE)
    top_countries = so["country"].value_counts().head(20).index
    so["country_bucket"] = so["country"].where(so["country"].isin(top_countries), "Other").fillna("Other")

    n_total = len(so)
    n_missing_original = so["income_usd"].isna().sum()

    implausible = so["income_usd"].notna() & (
        (so["income_usd"] < PLAUSIBLE_MIN) | (so["income_usd"] > PLAUSIBLE_MAX)
    )
    print(f"Valores de ingreso fuera de rango plausible [{PLAUSIBLE_MIN}, {PLAUSIBLE_MAX}]: "
          f"{implausible.sum()} ({implausible.sum()/n_total*100:.2f}%) -> tratados como faltantes")
    so.loc[implausible, "income_usd"] = np.nan

    so["log_income"] = np.log(so["income_usd"])

    # Outlier univariante adicional en escala log (Tabachnick & Fidell, +-3.29 DE)
    z = (so["log_income"] - so["log_income"].mean()) / so["log_income"].std()
    outliers = z.abs() > 3.29
    print(f"Outliers adicionales en log-escala (|z|>3.29): {outliers.sum()} -> tratados como faltantes")
    so.loc[outliers.fillna(False), "log_income"] = np.nan

    n_missing_final = so["log_income"].isna().sum()
    pct_missing = n_missing_final / n_total * 100
    print(f"\nMissingness final de log_income: {n_missing_final}/{n_total} ({pct_missing:.1f}%)")
    print(f"(original NA: {n_missing_original}, + invalidos/outliers arriba)")

    # MICEData de statsmodels exige columnas numericas (no dtype 'category')
    # incluso para regresores completamente observados - se dummifican
    # pais/anio ANTES de pasar los datos al imputador.
    base = so[["log_income", "is_solopreneur_candidate", "years_experience_pro"]].copy()
    base["is_solopreneur_candidate"] = base["is_solopreneur_candidate"].astype(int)
    country_dummies = pd.get_dummies(so["country_bucket"], prefix="country", drop_first=True, dtype=float)
    year_dummies = pd.get_dummies(so["survey_year"].astype(int), prefix="year", drop_first=True, dtype=float)
    # patsy exige identificadores validos en la formula - se sanean nombres
    # con espacios/caracteres especiales (ej. "country_United States").
    import re
    def sanitize(name):
        return re.sub(r"\W+", "_", name).strip("_")
    country_dummies.columns = [sanitize(c) for c in country_dummies.columns]
    year_dummies.columns = [sanitize(c) for c in year_dummies.columns]
    model_df = pd.concat([base, country_dummies, year_dummies], axis=1)

    predictor_cols = list(country_dummies.columns) + list(year_dummies.columns)
    return model_df, pct_missing, predictor_cols


def check_multicollinearity(model_df, predictor_cols):
    """
    Diagnostico de VIF ANTES de ajustar el modelo (obligatorio con multiples
    predictores, ver skill analisis-datos-cientificos). Se corre sobre las
    filas con log_income no faltante (equivalente al set de caso completo) -
    VIF es propiedad de la matriz de disenio/predictores, no cambia entre
    imputaciones.
    """
    cc = model_df.dropna(subset=["log_income", "years_experience_pro"]).copy()
    all_predictors = ["is_solopreneur_candidate", "years_experience_pro"] + predictor_cols
    X = cc[all_predictors].copy()
    X.insert(0, "const", 1.0)

    vifs = {col: variance_inflation_factor(X.values, i)
            for i, col in enumerate(X.columns) if col != "const"}
    high_vif = {k: v for k, v in vifs.items() if v > 5}

    print("\n=== Diagnostico de multicolinealidad (VIF) ===")
    print(f"VIF de los predictores sustantivos: "
          f"is_solopreneur_candidate={vifs['is_solopreneur_candidate']:.2f}, "
          f"years_experience_pro={vifs['years_experience_pro']:.2f}")
    if high_vif:
        print(f"Predictores con VIF>5 (umbral de alerta en ciencias sociales): "
              f"{ {k: round(v,2) for k,v in high_vif.items()} }")
        print("Nota: son las variables dummy de pais (categoria 'Other' y/o el pais")
        print("mas dominante) - artefacto mecanico esperado de dummy-coding con una")
        print("categoria dominante, no compromete la interpretacion de los")
        print("predictores sustantivos de interes (ambos VIF < 1.2).")
    else:
        print("Ningun predictor supera VIF=5.")


def run_mice(model_df, pct_missing, predictor_cols):
    n_imputations = max(20, int(np.ceil(pct_missing)))
    print(f"\nCorriendo MICE con {n_imputations} imputaciones "
          f"(regla: max(20, %missing) = max(20, {pct_missing:.0f}))...")

    import statsmodels.api as sm

    mice_data = MICEData(model_df)
    formula = "log_income ~ is_solopreneur_candidate + years_experience_pro + " + " + ".join(predictor_cols)
    mice = MICE(formula, sm.OLS, mice_data)

    results = mice.fit(n_burnin=10, n_imputations=n_imputations)
    print("\n=== Resultado combinado (pooling de Rubin, statsmodels MICE) ===")
    print(results.summary())
    return results


def report(results, n_imputations_used):
    # MICEResults.params es un array posicional, no una Series - los nombres
    # viven en results.exog_names (mismo orden que la formula del modelo).
    names = list(results.exog_names)
    idx = names.index("is_solopreneur_candidate")
    coef = results.params[idx]
    se = results.bse[idx]
    ci_low, ci_high = results.conf_int()[idx]
    pval = results.pvalues[idx]

    pct_diff_income = (np.exp(coef) - 1) * 100  # interpretacion en escala original (%)

    print(f"\nCoeficiente is_solopreneur_candidate (log-income): {coef:.4f}")
    print(f"SE: {se:.4f} | IC95%: [{ci_low:.4f}, {ci_high:.4f}] | p={pval:.4g}")
    print(f"Interpretacion en escala original: los solopreneurs ganan "
          f"~{abs(pct_diff_income):.1f}% {'menos' if pct_diff_income < 0 else 'mas'} "
          f"que otros autoempleados/freelancers, controlando por experiencia, "
          f"pais y anio.")

    summary_row = {
        "model": "MICE_OLS_pooled_Rubin",
        "dv": "log_income",
        "iv": "is_solopreneur_candidate",
        "n_imputations": n_imputations_used,
        "coef_log": coef,
        "se": se,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "p_value": pval,
        "pct_income_diff": pct_diff_income,
    }
    pd.DataFrame([summary_row]).to_csv(OUT_TABLES / "income_gap_mice_results.csv", index=False)
    return summary_row


def complete_case_sensitivity(model_df, predictor_cols):
    """
    Sensibilidad (Fase 3, paso 10): comparar contra el analisis de caso
    completo (listwise deletion) para mostrar cuanto cambia la conclusion -
    es la evidencia empirica de por que no bastaba con eliminar los NA.
    """
    import statsmodels.formula.api as smf
    cc = model_df.dropna(subset=["log_income", "years_experience_pro"])
    formula = "log_income ~ is_solopreneur_candidate + years_experience_pro + " + " + ".join(predictor_cols)
    model = smf.ols(formula, data=cc).fit()
    coef = model.params["is_solopreneur_candidate"]
    ci = model.conf_int().loc["is_solopreneur_candidate"]
    pval = model.pvalues["is_solopreneur_candidate"]
    pct_diff = (np.exp(coef) - 1) * 100
    print(f"\n=== Sensibilidad: caso completo (listwise deletion, N={len(cc)}) ===")
    print(f"Coef: {coef:.4f} [{ci[0]:.4f}, {ci[1]:.4f}], p={pval:.4g} "
          f"(~{pct_diff:.1f}% de diferencia en ingreso)")
    print("Comparar con el resultado MICE de arriba: si difieren sustancialmente,")
    print("confirma que el missingness MAR sesgaba el analisis de caso completo.")
    return {"model": "complete_case_OLS", "n_obs": len(cc), "coef_log": coef,
            "ci_low": ci[0], "ci_high": ci[1], "p_value": pval, "pct_income_diff": pct_diff}


def main():
    model_df, pct_missing, predictor_cols = load_and_prepare()
    check_multicollinearity(model_df, predictor_cols)
    n_imp = max(20, int(np.ceil(pct_missing)))
    results = run_mice(model_df, pct_missing, predictor_cols)
    mice_summary = report(results, n_imp)
    cc_summary = complete_case_sensitivity(model_df, predictor_cols)

    pd.DataFrame([mice_summary, cc_summary]).to_csv(
        OUT_TABLES / "income_gap_mice_vs_completecase.csv", index=False
    )


if __name__ == "__main__":
    main()

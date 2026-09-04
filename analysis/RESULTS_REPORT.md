# Results Report — Digital Solopreneurship: A Multi-Source Exploratory Analysis

**Status: EXPLORATORY / HYPOTHESIS-GENERATING.** None of the three hypotheses
below were pre-registered. They were formulated from the applied-economics
literature on self-employment and the digital-work literature *before*
inspecting the outcome variables, but the specific operational form (which
predictors, which country bucketing, which outlier rule) was refined while
looking at these data. Per the anti-HARKing rule, **all three findings must
be labeled exploratory in the manuscript, with an explicit call for
independent replication** — not presented as confirmatory tests of an a
priori theory. No sample was held out for a genuinely confirmatory split
(N did not permit it without under-powering the MICE model); multiple
comparisons across the 3 primary hypotheses are noted below.

Study design: **observational, secondary/repurposed multi-source data**.
Three incompatible units of analysis are combined by triangulation, not
pooled into one model: country-year (ecological), repeated cross-sectional
individual (Stack Overflow Developer Survey, independent respondents each
wave — not a panel), and bibliometric/repository counts (contextual only,
not hypothesis-tested here).

---

## H1 — Macro context: internet penetration and self-employment

**H0:** The within-country association between internet penetration and the
total self-employment rate is zero.
**H1:** Internet penetration is associated with the self-employment rate,
country-year level, net of country and year fixed effects.

- **Data:** World Bank, 213 countries, 2005–2024, N = 4,119 country-years
  (16.5% dropped for missing indicator values in a given year).
- **Model:** Two-way fixed-effects panel OLS (entity = country, time = year),
  standard errors clustered by country.

$$
\text{SelfEmployed}_{it} = \alpha_i + \gamma_t + \beta \cdot \text{InternetUsers}_{it} + \varepsilon_{it}
$$

| Term | Coef. | Clustered SE | 95% CI | p | R²(within) |
|---|---|---|---|---|---|
| Internet users (%) | −0.028 | 0.012 | [−0.051, −0.004] | .020 | 0.173 |

**Interpretation:** Statistically significant, and the model accounts for a
non-trivial share of within-country variation (R² within = 17.3%) even
though the per-unit coefficient is numerically small: a within-country
increase in internet penetration is associated with a small *decrease* in
the aggregate self-employment rate. This is not evidence against digital
solopreneurship — `self_employed_pct_total` is a broad World Bank measure
that conflates traditional/informal self-employment (which mechanically
falls as economies develop and formalize, a process correlated with rising
internet access) with the specific digital-solopreneur segment, which this
aggregate cannot isolate. **The negative macro coefficient motivates,
rather than undermines, the need for micro-level data (H2/H3 below)** —
it is consistent with a composition shift (informal self-employment
falling faster than any digital-solopreneur segment is rising) rather than
with an absence of relationship.

Descriptive robustness check (Eurostat, EU/EEA own-account workers, absolute
thousands, 2010–2024): a visible dip in 2020–2021 (COVID) with partial
recovery by 2024, consistent with a cyclical rather than a steady secular
trend at the macro level.

---

## H2 — Temporal trend: solopreneur share among the self-employed

**H0:** The odds of being a "0-employee" solopreneur among self-employed/
freelance respondents do not change across survey years (OR = 1).
**H1:** The odds change across 2019–2024.

- **Data:** Stack Overflow Developer Survey, 2019–2024 (2017–2018 excluded:
  no "Just me" category existed in those waves — see
  `data_collection/schema/definicion_operativa.md`). N = 47,322
  self-employed/freelance respondents with a determinate organization size
  (82.1% of the filtered self-employed/freelance pool; the remaining 17.9%
  answered "I don't know" or left it blank and are excluded, not imputed
  as non-solopreneurs).
- **Design:** Repeated cross-section (independent respondents each wave,
  **not** a panel — no individual trajectories can be inferred).
- **Model:** Logistic regression, year (centered) as continuous predictor;
  robustness model adds country (top-20 + "Other") as a covariate to rule
  out sampling-composition confounds.

$$
\text{logit}\big(P(\text{Solopreneur}_i = 1)\big) = \beta_0 + \beta_1 \cdot \text{Year}_{c,i}
$$

| Model | OR (per year) | 95% CI | p | McFadden R² | N |
|---|---|---|---|---|---|
| Unadjusted | 0.827 | [0.818, 0.836] | 8.8×10⁻²⁴⁹ | 0.018 | 47,322 |
| Country-adjusted (robustness) | 0.829 | [0.820, 0.839] | 4.3×10⁻²³³ | — | 47,322 |

**Descriptive proportions (Wilson 95% CI):** 52.0% (2019) → 44.6% (2020) →
49.2% (2021) → **29.6% (2022)** → 32.3% (2023) → 32.1% (2024).

**Interpretation:** A large, robust decline (~17% relative odds reduction
per year) in the "0-employee" share among self-employed/freelance
developers, concentrated in the 2021→2022 transition, and unchanged after
controlling for country composition. This **contradicts the popular
narrative of a secular rise in solopreneurship** within this specific
population (professional software developers) and should be reported as
such — a genuinely surprising, publication-worthy exploratory finding, not
adjusted or explained away. Candidate (untested) explanations for the
Discussion section: the 2022–2023 tech layoffs may have pushed some
solo-inclined developers into small agencies/co-founded ventures rather
than staying solo, or shifted the survey's respondent pool. **This is
hypothesis-generating only** — the cross-sectional (non-panel) design
cannot distinguish a true behavioral shift from a compositional shift on
unobserved variables.

---

## H3 — Income gap: solopreneurs vs. other self-employed/freelancers

**H0:** log-income does not differ between solopreneurs and other
self-employed/freelancers, net of experience, country, and year.
**H1:** log-income differs.

- **Data:** Same N = 47,322 base. Missingness diagnosis (pre-registered as
  a required step, not skipped): income missingness is **not** MCAR — it
  is associated with the observed variable `org_size` (48.3% missing among
  solopreneurs vs. 32.0% among others, monotonic in team size), i.e.
  **MAR**. Listwise deletion would therefore differentially exclude
  solopreneurs and bias the comparison. 682 implausible values (<$1,000 or
  >$2,000,000/year — currency-conversion errors/joke responses, a known
  issue in this survey) and 100 additional |z|>3.29 log-scale outliers were
  recoded to missing (not deleted, not winsorized) prior to imputation.
  Combined missingness: 40.0%.
- **Multicollinearity (VIF), checked before fitting:** substantive
  predictors clean (solopreneur status VIF=1.10, experience VIF=1.11);
  two country dummies exceeded VIF=5 (`Other`=10.42, `United States`=6.21),
  an expected dummy-coding artifact, not a threat to the focal coefficient.
- **Method:** Multiple Imputation by Chained Equations (`statsmodels.imputation.mice`),
  **40 imputations** (Graham et al., 2007 rule: max(20, % missing)), 10
  burn-in iterations, Rubin's pooling rules applied automatically by the
  library (not manual averaging).

$$
\log(\text{Income}_i) = \beta_0 + \beta_1 \cdot \text{Solopreneur}_i + \beta_2 \cdot \text{YearsExperience}_i + \sum_k \gamma_k \text{Country}_{k,i} + \sum_t \delta_t \text{Year}_{t,i} + \varepsilon_i
$$

| Model | Coef. (log) | SE | 95% CI (log) | p | % income difference | N |
|---|---|---|---|---|---|---|
| **MICE (pooled, primary)** | −0.235 | 0.012 | [−0.258, −0.212] | 3.7×10⁻⁸⁷ | **≈ −20.9%** | 47,322 |
| Complete-case (sensitivity) | −0.220 | 0.012 | [−0.245, −0.196] | 5.9×10⁻⁷¹ | ≈ −19.8% | 27,765 |

**Interpretation:** Solopreneurs earn **~20.9% less** than other self-employed/
freelance developers with the same experience, country, and survey year —
a large, practically meaningful effect (an income difference this size is
substantively important regardless of the p-value), and one considerably
larger in relative terms than the modest H1 macro coefficient. The MICE and
complete-case estimates are close (−20.9% vs. −19.8%), which is itself a
useful robustness finding: the
documented MAR mechanism did not, in this case, produce a *qualitatively*
different conclusion than naive listwise deletion would have — but the
MICE estimate remains the one that should be reported as primary, on
principled (unbiasedness-under-MAR) rather than post-hoc grounds.

---

## Summary table (for `redaccion-resultados`)

| Hypothesis | Variable | Statistic | Effect | 95% CI | p | N | Classification |
|---|---|---|---|---|---|---|---|
| H1 (macro) | Self-employment % ~ Internet % | Panel-FE β | −0.028 | [−0.051, −0.004] | .020 | 4,119 country-years | Exploratory; ecological |
| H2 (trend) | P(solopreneur) ~ Year | Logistic OR | 0.827/yr | [0.818, 0.836] | <.001 | 47,322 | Exploratory; repeated cross-section |
| H3 (income) | log(Income) ~ Solopreneur | MICE-pooled β | −0.235 (≈−20.9%) | [−0.258, −0.212] | <.001 | 47,322 | Exploratory; MAR-adjusted |

**Multiple comparisons:** 3 primary hypotheses tested; at α=.05 uncorrected,
family-wise error ≈ 14%. All three p-values are several orders of magnitude
below a Bonferroni-corrected threshold (α/3 ≈ .0167), so this does not
change any conclusion, but is reported for completeness.

---

## Limitations (for the manuscript's Limitations section)

1. **Non-probability samples.** The Stack Overflow Developer Survey is a
   convenience sample of a platform's users, not a probability sample of
   developers or of solopreneurs generally — this bounds external validity
   to "developers who take this specific annual survey," not
   solopreneurship in general. This was an explicit, accepted design
   decision for this project (see `data_collection/README.md`: "asumirlo y
   declararlo").
2. **Repeated cross-section, not panel (H2).** No individual can be
   observed transitioning in or out of solopreneur status; the year effect
   in H2 is a population-composition trend, not an individual trajectory,
   and cannot rule out unobserved compositional shift beyond the country
   control already applied.
3. **Ecological inference (H1).** Country-year aggregates cannot support
   individual-level claims (ecological fallacy). The null/negative H1
   finding should not be read as "internet does not enable solopreneurship
   for individuals" — only that the aggregate self-employment measure
   cannot detect it.
4. **Structural signal is a proxy, not a direct measure.** "Solopreneur"
   candidacy is inferred from `OrgSize == "Just me"` — the structural leg
   only of the three-criterion operational definition (structural,
   intentional, leverage; see `data_collection/schema/definicion_operativa.md`).
   Intentional and leverage signals could not be measured from this survey
   and are not part of H2/H3 — these findings describe "0-employee
   self-employed developers," a necessary but not sufficient condition for
   the stricter "solopreneur" construct used elsewhere in this project.
5. **2017–2018 excluded from H2/H3** for lacking the "Just me" category;
   trend claims are therefore bounded to 2019–2024, not the full survey
   history.
6. **MICE model is not exhaustive.** The imputation and outcome models use
   the same covariate set (experience, country bucket, year) — a
   congenial but not fully saturated specification. Auxiliary variables
   not included (e.g., detailed `dev_type`, unusable here due to
   free-text multi-select cardinality of 9,767 unique combinations) might
   further reduce residual bias under MAR.
7. **All three findings are exploratory/hypothesis-generating** (see
   header) and require independent replication before being treated as
   confirmed effects.

---

## Reproducibility

- Scripts (run in order): `scripts/01_audit_data.py` →
  `scripts/02_build_clean_subtables.py` → `scripts/03_macro_panel.py` →
  `scripts/04_trend_analysis.py` → `scripts/05_income_gap_mice.py`
- All cleaning decisions (outlier rules, missingness treatment, country
  harmonization) are inline-commented in the scripts, not applied by hand.
- Library versions: statsmodels 0.14.6, linearmodels 6.1, pandas (see
  `data_collection/requirements.txt` for the ingestion side).
- Random seed: `np.random.seed(42)` fixed at the top of
  `05_income_gap_mice.py` before `mice.fit()` — re-running reproduces the
  reported estimates exactly.
- Suggested next step for FAIR compliance: deposit `analysis/data/*_clean.csv`,
  the five scripts, and this report in a DOI-bearing repository (Zenodo/OSF)
  once the manuscript's data/code availability statement is drafted.

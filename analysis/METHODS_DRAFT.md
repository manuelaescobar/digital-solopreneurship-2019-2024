# Methods

*[Section name: "Methods" is used by default; rename to "Materials and*
*Methods" if the target journal's author guidelines require it — to be*
*confirmed once a journal is selected.]*

## Design

This study used an observational, secondary-data design combining three
levels of analysis that were triangulated rather than pooled: a
country-year macro panel, a repeated cross-sectional individual-level
survey, and a bibliometric corpus (the latter reported descriptively only
and not tested against a hypothesis in this manuscript). No data were
collected for the purpose of this study; all sources were public,
pre-existing datasets accessed through their official APIs.

## Operational Definition of Solopreneur

"Solopreneur" was operationalized using three criteria established prior
to data collection: a structural criterion (zero employees), an
intentional criterion (no expressed intention to grow via headcount), and
an income-leverage criterion (income decoupled from hours worked, e.g.,
through a product or digital asset rather than billed time). Of the three,
only the structural criterion could be measured in the individual-level
survey used for H2 and H3, operationalized as the response "Just me — I am
a freelancer, sole proprietor, etc." to the organization-size item. This
means the label "solopreneur" in the H2/H3 results should be read
narrowly as "zero-employee self-employed/freelance respondent," a
necessary but not sufficient condition for the fuller three-part
construct; this scoping is treated as a substantive limitation, not a mere
caveat, in the Conclusions.

## Data Sources and Samples

**Macro panel (H1).** Country-year indicators were drawn from the World
Bank Open Data API (no authentication required): self-employment as a
percentage of total employment (indicator SL.EMP.SELF.ZS) and internet
users as a percentage of population (IT.NET.USER.ZS), for all available
countries, 2005–2024. Regional and income-group aggregates published
alongside individual countries (e.g., "High income") were identified via
a missing standard ISO-3 country code and excluded from the country-level
panel. Country-years missing either indicator were excluded listwise,
yielding a final panel of 4,119 country-years across 213 countries. A
descriptive robustness check used Eurostat's own-account-worker series
(dataset `lfsa_esgais`, occupation category `TOTAL`, sex `T`, age
`Y_GE15`) for European Economic Area countries, 2010–2024, retrieved via
the Eurostat REST API.

**Individual-level sample (H2, H3).** Individual-level data came from six
consecutive annual waves (2019–2024) of the Stack Overflow Developer
Survey, a self-selected convenience sample of respondents to a single
technology platform's annual survey, obtained as public CSV files
(2011–2024 archive, mirrored on Kaggle). The analytic sample was
restricted to respondents who (a) reported an employment status of
"Independent contractor, freelancer, or self-employed" and (b) provided a
determinate response to the organization-size item (excluding "I don't
know" and missing responses, which were treated as missing rather than
coded as non-solopreneur). This yielded *N* = 47,322 respondents (82.1%
of the self-employed/freelance respondent pool across the six waves).
Survey waves 2017–2018 were excluded from H2/H3 because those years' organization-size item did not include a zero-employee ("Just me") category,
making the structural criterion unobservable in those waves.

## Measures

*Self-employment rate* and *internet penetration* (H1) were used as
published by the World Bank, expressed as percentages. *Solopreneur
status* (H2, H3) was a binary indicator derived from the organization-size
item as described above. *Annual income* (H3) was drawn from each wave's
income item (`ConvertedCompYearly`/`ConvertedComp`/`Salary`, depending on
survey year), converted to USD by the survey provider, and log-transformed
prior to analysis to address right skew. *Professional experience* (H3)
was the self-reported years of professional coding experience
(`YearsCodePro`/`YearsCodedJob`). *Country* (H2 robustness check, H3) was
self-reported; inconsistent naming of the same country across survey
years (e.g., "United States" versus "United States of America") was
harmonized to a single label prior to analysis, and the resulting variable
was recoded into the 20 most-represented countries plus a residual
"Other" category for use as a covariate.

## Data Quality Procedures

Three data-quality issues were identified and addressed prior to analysis,
each documented in the analysis code rather than corrected by hand.
First, annual income values outside a plausible range for professional
software developers (< $1,000 or > $2,000,000 USD/year, *n* = 682, 1.4% of
the analytic sample) — a known issue in this survey attributable to
currency-conversion errors and implausible entries — were recoded to
missing rather than deleted or capped, followed by removal of additional
log-scale outliers (|*z*| > 3.29, Tabachnick & Fidell criterion; *n* =
100). Second, the missing-data mechanism for income was diagnosed before
choosing a treatment: missingness was associated with the observed
organization-size variable (48.3% missing among zero-employee respondents
versus 32.0% among respondents with larger organizations, monotonically
decreasing with organization size), indicating a Missing at Random (MAR)
rather than Missing Completely at Random mechanism, which ruled out
listwise deletion (would have removed 40.0% of the analytic sample
non-randomly) and simple mean/median imputation (would underestimate
variance and bias inference) in favor of multiple imputation (see Analytic
Strategy). Third, multicollinearity among the H3 regression's predictors
was checked via variance inflation factor (VIF) before fitting: the two
substantive predictors were unaffected (solopreneur status, VIF = 1.10;
years of experience, VIF = 1.11), while the residual "Other" country
category (VIF = 10.42) and the single largest country category, United
States (VIF = 6.21), exceeded conventional thresholds — an expected
consequence of dummy-coding a covariate with one dominant category and a
large residual bucket, and not judged to threaten inference on the focal
solopreneur coefficient.

## Analytic Strategy

All three hypotheses reported in Results were formulated from applied
labor-economics reasoning prior to inspecting the corresponding outcome
variables, but their exact operational form (predictor coding, outlier
rules, covariate sets) was finalized while working with these data;
accordingly, all three are reported as exploratory/hypothesis-generating
findings requiring independent replication, not as confirmatory tests of
pre-registered hypotheses (no pre-registration exists for this study).

For H1, a two-way fixed-effects panel regression (entity = country, time =
year) was fit with standard errors clustered by country, implemented with
`linearmodels.PanelOLS`, to isolate within-country covariation between
internet penetration and the self-employment rate net of time-invariant
country characteristics and common annual shocks. For H2, a logistic
regression with mean-centered survey year as a continuous predictor was
fit to test for a linear trend in the log-odds of solopreneur status
across waves, followed by a robustness model adding country (20 most-
represented plus "Other") as a covariate to rule out a sampling-
composition confound. For H3, given the MAR missingness mechanism
established above, Multiple Imputation by Chained Equations (MICE;
`statsmodels.imputation.mice`) was used to impute log-income. Graham et
al. (2007) recommend, based on simulation evidence tolerating no more than
a 1% loss of power, 20 imputations for 10–30% missing information and 40
for 50%; given observed missingness of 40.0%, 40 imputations were used as
the conservative choice between these two benchmarks, with 10 burn-in
iterations per chain. Parameter estimates across imputations were combined using Rubin's
rules, implemented automatically by the library rather than by manual
averaging. A complete-case ordinary least squares model on the same
specification was fit as a sensitivity check against the primary,
multiply imputed estimate.

## Statistical Power

Because this study uses existing secondary data rather than a sample
collected for this purpose, sample-size adequacy was assessed post hoc
rather than through an a priori power calculation. Following Cohen's
(1988) convention for the general linear F-test, the achieved samples
provide power exceeding .999 (α = .05) to detect even a small effect
(*f*² = .01) for the individual-level models (*N* = 47,322, up to 27
model terms) and power exceeding .999 to detect the macro panel model's
observed effect size (*f*² = .209, corresponding to the reported *R*²
within = .173, *N* = 4,119). Statistical power was therefore not a binding
constraint on any of the three analyses; the more consequential threats to
inference in this study are the non-probability nature of the individual-
level sample and the repeated cross-sectional (non-panel) design, both
addressed in the Conclusions.

## Software and Reproducibility

All data retrieval, cleaning, and analysis steps were implemented as
version-controlled Python scripts (Python 3.9; pandas, statsmodels 0.14.6,
linearmodels 6.1, scikit-learn, scipy), executed end-to-end without manual
data editing. A fixed random seed (`np.random.seed(42)`) was set prior to
the MICE procedure to ensure exact reproducibility of the reported
estimates. Code and cleaned (de-identified, aggregate/survey-response
level, no personally identifying information) data are available at
[repository URL / DOI — to be added at submission, per the Data and Code
Availability Statement].

---

See `REFERENCES.md` for the consolidated, manuscript-wide reference list
(includes Cohen, 1988, and Graham et al., 2007, cited in this section).

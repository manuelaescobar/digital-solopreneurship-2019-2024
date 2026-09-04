# Editorial Statements

*Placement note: several journals put some of these in Methods (Data/Code*
*Availability), others in Acknowledgments (AI use), others as standalone*
*end-of-manuscript sections — confirm exact placement/headings against the*
*target journal's author guidelines once selected.*

## Funding Statement

> This research received no external funding.

## Ethical Compliance

> This study used only publicly available, aggregate or already
> de-identified secondary data (World Bank Open Data, Eurostat, U.S.
> Census Bureau Nonemployer Statistics, GitHub public repository metadata,
> OpenAlex bibliometric records, and the publicly released, de-identified
> Stack Overflow Developer Survey microdata). No new data were collected
> from human participants by the authors, and no personally identifying
> information was accessed. [CONFIRM: your institution's policy on
> whether an exempt/not-human-subjects determination must still be
> formally recorded for secondary-data studies — this varies by
> institution even when the reasoning above is straightforward.]

This is drafted with real, verifiable facts about the data sources
actually used in this project — but I flagged the bracketed confirmation
because IRB/ethics-committee policies on formal exemption paperwork for
secondary-data studies vary by institution, and I cannot know your
institution's specific requirement.

## Data Access Statement

> Macro-level data are publicly available from their original sources:
> World Bank Open Data (https://data.worldbank.org), Eurostat
> (https://ec.europa.eu/eurostat), and U.S. Census Bureau Nonemployer
> Statistics (https://www.census.gov/programs-surveys/nonemployer-statistics.html).
> Individual-level data are from the Stack Overflow Developer Survey,
> publicly archived at https://survey.stackoverflow.co and mirrored on
> Kaggle. The cleaned, analysis-ready datasets and code used to produce
> them are available at [REPOSITORY/DOI — pending deposit; see Code
> Availability below].

The source URLs above are real and match what this project actually used.
The bracketed repository/DOI is pending because the cleaned data has not
yet been deposited anywhere with a permanent identifier.

## Code Availability Statement

> All data collection, cleaning, and analysis code is available at
> [REPOSITORY URL/DOI — e.g., GitHub with a Zenodo-issued DOI]. The
> pipeline runs end-to-end from raw API ingestion through the reported
> statistical models without manual data editing.

**Action needed before this can be finalized**: the project currently
lives only in local folders (`data_collection/`, `analysis/`), not in a
version-controlled, publicly hosted repository. Depositing it (e.g.,
GitHub → Zenodo for a DOI) is a prerequisite for this statement to be true
rather than aspirational — I can help set this up when you're ready.

## Conflict of Interest Declaration

> The authors declare no conflict of interest.

## CRediT Author Contribution Statement

> **Yurleidy Cossio-Restrepo**: Conceptualization, Investigation, Writing –
> review & editing.
> **Manuela Escobar-Sierra**: Conceptualization, Methodology, Software,
> Formal analysis, Data curation, Writing – original draft, Writing –
> review & editing, Visualization.
> **Francisco Javier Arias Vargas**: Conceptualization, Investigation,
> Validation, Writing – review & editing.

**This allocation is a draft, not a verified fact, and I want to be
explicit about its basis.** I cannot know what each of you actually did on
this specific paper — I only directly observed Manuela's session, in
which essentially all data collection, cleaning, modeling, and drafting
was executed (with AI assistance, disclosed above). The roles for
Yurleidy and Francisco above are inferred from their public ORCID
research profiles, not from any evidence of actual contribution to this
manuscript:
- **Yurleidy Cossio-Restrepo** (Economics, Administrative and Accounting
  Sciences, Universidad Tecnológica del Chocó) — public research focuses
  on community well-being and territory measurement models, including at
  least one apparent prior collaboration with Manuela Escobar-Sierra on
  related measurement-model work.
- **Francisco Javier Arias Vargas** (PhD in Business Administration and
  Management) — public research record centers on entrepreneurship
  ecosystems, business models, and governance, with prior work validating
  measurement questionnaires.

CRediT is meant to reflect real, verifiable contribution — assigning a
role to someone who did not actually perform it is a misrepresentation,
not a formality, and journals increasingly check this. **Please correct
each person's roles to match what actually happened** before this is
finalized; treat what's above as a plausible starting point drawn from
public expertise, not a claim I'm making on your behalf about real events
I did not witness.

## Declaration of Generative AI Use

> During the preparation of this work, the author(s) used Claude (Claude
> Code, Anthropic) for: (1) designing and implementing the data-collection
> pipeline across six public data sources (API clients, ingestion scripts,
> and cross-source schema normalization); (2) data cleaning, including
> outlier detection, missing-data mechanism diagnosis, and multicollinearity
> checks; (3) implementation and execution of all statistical models
> reported (panel fixed-effects regression, logistic regression, and
> multiple imputation by chained equations); (4) drafting of the Methods,
> Results, Discussion, and Conclusions text; and (5) an initial literature
> search to identify candidate citations for the Discussion and
> Conclusions, which the author(s) must independently verify against
> primary sources before submission. The author(s) reviewed, verified
> against source data, and edited all AI-assisted content, and take full
> responsibility for the accuracy and validity of the analysis and text in
> this publication.

**This one I can write with full honesty because I did the work being
disclosed.** I deliberately did not soften it to "language editing" —
that would misrepresent what actually happened. The level of AI
involvement here (building the entire ingestion-to-inference pipeline, not
just polishing prose) is substantial enough that, before submission, you
should be able to independently explain and reproduce every step
yourself — a reviewer or editor may reasonably ask about it given how
central AI use was to this project, and "the AI did it" is never an
acceptable answer to a methods question. I already flagged the citations
specifically as needing your independent verification, since that risk
(plausible-sounding but wrong references) is the one most likely to slip
through unnoticed.

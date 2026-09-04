# Solopreneur — Extracción Masiva de Datos

Pipeline de recolección para el estudio de solopreneurs digitales (negocio
de una sola persona, sin intención de crecer vía nómina, ingresos
desacoplados de horas trabajadas — ver `schema/definicion_operativa.md`).

## Estado de cumplimiento por fuente (verificado en vivo, 2026-09-02)

| Fuente | Estado | Vía |
|---|---|---|
| OpenAlex | ✅ Activo, probado (826 papers reales) | API REST abierta, sin key |
| World Bank | ✅ Activo, probado (1169 obs. país-año) | API REST abierta, sin key |
| Eurostat | ✅ Activo, probado (1030 obs., incluye `SELF_NS`=own-account workers) | API REST abierta, sin key |
| GitHub | ✅ Activo, probado (repos por topic indie-hacker/microsaas/etc.) | Search API pública; sin token 10 req/min, con Personal Access Token propio (auto-generado, sin app/captcha) 30 req/min |
| Census NES | ✅ Activo, probado (204 obs., 51 estados × 4 sectores NAICS) | API oficial, key gratis por email (la key tarda unos minutos en activarse tras el registro) |
| Stack Overflow Survey | ✅ Activo, probado (72,174 respuestas self-employed/freelancer, 2017-2024) | Kaggle vía `kagglehub`, sin credenciales — más simple que la descarga manual del sitio oficial (que es una SPA sin link de descarga estático). Ver nota abajo. |
| Product Hunt | ⏸️ Pausado por fricción de cuenta | API GraphQL oficial — retomar cuando puedas crear el Developer Token |
| Reddit | ⏸️ Pausado por fricción de cuenta | API oficial (PRAW) — bloqueado en la creación de la app (captcha/verificación de cuenta), retomar cuando se resuelva |
| ILOSTAT | ⏸️ Pausado | Igual que Flippa: el bulk download está detrás de un reto activo de Cloudflare. No lo evadimos. Cubierto parcialmente por World Bank (estimaciones ILO modeladas) mientras tanto. |
| Indie Hackers | ❌ No se scrapea | Sus Términos de Servicio prohíben explícitamente "crawls, scrapes, or spiders" cualquier página o dato del servicio. Ver alternativas abajo. |
| Flippa | ⏸️ Pausado | robots.txt lo permite, pero el sitio sirve un reto JS de Cloudflare a peticiones automatizadas simples. Evadirlo requeriría técnicas de fingerprint evasion que no vamos a construir. Ver alternativas abajo. |

**Regla del proyecto**: antes de añadir una fuente nueva, se verifica
`robots.txt` + Términos de Servicio + si hay protección anti-bot activa.
Si el ToS prohíbe scraping explícitamente, o hay que evadir protección
técnica activamente, la fuente no entra por esta vía — se busca API oficial,
dataset ya publicado, o colaboración directa con la plataforma.

## Alternativas para Indie Hackers y Flippa

- **Indie Hackers**: no tiene API pública. Opciones legítimas:
  1. Contactar al equipo pidiendo acceso de investigación (varias plataformas
     lo conceden a académicos).
  2. Reddit r/indiehackers como proxy parcial del discurso (ya cubierto por
     `reddit_ingest.py`).
  3. Snapshots históricos vía Common Crawl (no golpea los servidores de IH,
     usa el archivo público de Common Crawl) — factible pero de menor
     cobertura y calidad; lo evalúo si hace falta más adelante.
- **Flippa**: opciones legítimas:
  1. Empire Flippers e Investors Club publican reportes agregados públicos
     (PDF/blog) con datos de transacciones reales — no requieren scraping.
  2. Si tienes cuenta propia en Flippa, exportar manualmente tus búsquedas
     guardadas (uso personal autenticado, bajo volumen) es distinto de
     scraping masivo automatizado.
  3. Contacto directo con Flippa para acceso de datos con fines de
     investigación.

## Estructura

```
data_collection/
  scripts/
    producthunt_ingest.py   # API GraphQL, pagina posts, filtra maker_count==1
    reddit_ingest.py        # PRAW, submissions+comments de subreddits objetivo
  schema/
    definicion_operativa.md # criterios de solopreneur usados para filtrar/etiquetar
    esquema_unificado.md    # diccionario de datos común entre fuentes
  data/
    raw/producthunt/        # JSON crudo, un archivo por corrida
    raw/reddit/             # JSON crudo, un archivo por subreddit/corrida
    processed/              # tablas limpias, formato parquet/csv
  logs/
```

## Stack Overflow Survey: descarga vía Kaggle (sin credenciales)

El sitio oficial (survey.stackoverflow.co) es una SPA sin link de descarga
estático en el HTML — no automatizable. En su lugar, el dataset completo
(2011-2024) está espejado publicamente en Kaggle y se descarga sin login:

```bash
pip install kagglehub
python3 -c "import kagglehub; print(kagglehub.dataset_download('joebeachcapital/stack-overflow-annual-developer-survey-2024'))"
```

Eso deja los CSV en `~/.cache/kagglehub/datasets/.../versions/N/`, uno
por año (`stack-overflow-developer-survey-<anio>/survey_results_public.csv`
para 2017-2024). Luego, por cada año:

```bash
python3 scripts/so_survey_process.py --input <ruta_al_csv> --year <anio>
```

**Limitación conocida**: 2017 y 2018 usan esquema de columnas distinto
(`EmploymentStatus`/`CompanySize` en vez de `Employment`/`OrgSize`) y esa
encuesta no ofrecía la categoría "Just me" — el bucket más fino era
"Fewer than 10 employees". El `structural_signal` para esos dos años es
por tanto más grueso; cada registro lo marca con
`org_size_granularity: "coarse_no_just_me_option"` para no comparar
prevalencia entre años sin esa salvedad.

## Normalización a tabla unificada

```bash
python3 scripts/normalize.py
```

Lee **todos** los archivos de `data/raw/<fuente>/*.json` (no solo el más
reciente — cada corrida de ingesta es un archivo nuevo con timestamp, y
para fuentes multi-año como Stack Overflow cada archivo es un año
distinto, no una versión más completa de la anterior), mapea cada
registro al esquema de `schema/esquema_unificado.md`, deduplica por
`entity_id`, y escribe:
- `data/processed/entities.csv` — tabla unificada completa
- `data/processed/summary_by_source.csv` — conteo por fuente

**Estado actual (última corrida)**: 98,112 filas — Stack Overflow Survey
(72,174 respuestas self-employed/freelancer 2017-2024, 18,231 candidatos
"Just me"), World Bank (23,224 obs. país-año), GitHub (1,135 repos),
OpenAlex (826 papers), Eurostat (549 obs. país-año), Census NES (204).

**Bugs de calidad de datos detectados y corregidos durante la
construcción** (se documentan porque son el tipo de error que pasa
inadvertido si no se audita el conteo antes/después de deduplicar):
1. Eurostat: el id no incluía la dimensión de ocupación (`isco08`),
   colapsando 12 desgloses ocupacionales distintos en un mismo país-año.
   Fix: filtrar `isco08=TOTAL` en el request.
2. World Bank: algunas filas (agregados como "High income", "Low income")
   traen `countryiso3code` vacío, colapsando geografías distintas con
   valores distintos bajo el mismo id. Fix: usar el id interno del país
   como respaldo cuando el iso3 viene vacío, y marcar `is_aggregate=true`
   en esas filas para poder excluirlas del análisis por país si se desea.
3. Stack Overflow Survey: `structural_signal` se calculaba a partir del
   campo `Employment`, que ya se había usado para filtrar la fila —
   resultado: el 100% de las filas filtradas salían "candidatas", sin
   distinguir a alguien realmente solo de quien dirige una agencia de
   1,000+ personas. Fix: usar únicamente `OrgSize` (o su alias por año)
   para la señal estructural.
4. `normalize.py` tomaba por defecto solo el archivo más reciente por
   fuente, lo cual descartaba silenciosamente 7 de los 8 años de Stack
   Overflow Survey (cada año es un archivo distinto, no una versión más
   completa de la anterior). Fix: procesar siempre todos los archivos;
   la deduplicación por `entity_id` ya resuelve con seguridad los casos
   donde una corrida sí superpone a otra.

## Setup

```bash
cd data_collection
python3 -m pip install -r requirements.txt
cp .env.example .env   # y completa tus credenciales
```

### Credenciales necesarias

**Product Hunt**
1. Crea una cuenta de desarrollador en https://api.producthunt.com/v2/oauth/applications
2. Crea una "aplicación" — te da un **Developer Token** que funciona directo
   para lectura pública (no necesitas completar el flujo OAuth de usuario).
3. Ponlo en `.env` como `PRODUCTHUNT_TOKEN`.

**Reddit**
1. Crea una app tipo "script" en https://www.reddit.com/prefs/apps
2. Copia `client_id` y `client_secret` a `.env` (`REDDIT_CLIENT_ID`,
   `REDDIT_CLIENT_SECRET`). Usa tu username de Reddit como `REDDIT_USER_AGENT`
   (ej. `solopreneur-research by u/tu_usuario`).

## Uso

```bash
# OpenAlex: mapeo bibliometrico del campo (no requiere credenciales)
python3 scripts/openalex_ingest.py --max-results 1000

# World Bank: series pais-anio de autoempleo/internet (no requiere credenciales)
python3 scripts/worldbank_ingest.py --start 2005 --end 2024

# Eurostat: own-account workers (SELF_NS) por pais europeo/anio (no requiere credenciales)
python3 scripts/eurostat_ingest.py --start 2010 --end 2024

# GitHub: repos por topic indie-hacker/microsaas/etc (funciona sin token,
# mejor con GITHUB_TOKEN propio generado en Settings > Developer settings)
python3 scripts/github_ingest.py --max-results 500

# Census NES: negocios sin empleados por sector/estado (requiere CENSUS_API_KEY)
python3 scripts/census_nes_ingest.py --year 2021 --geo state

# Stack Overflow Survey: requiere descargar el CSV manualmente primero
# desde https://survey.stackoverflow.co/<anio> (boton "Download the dataset",
# sin login) y luego:
python3 scripts/so_survey_process.py --input ~/Downloads/survey_results_public.csv --year 2024

# Product Hunt / Reddit (pausados, retomar cuando haya credenciales):
python3 scripts/producthunt_ingest.py --days 30
python3 scripts/reddit_ingest.py --limit 500
```

Cada corrida escribe un JSON con timestamp en `data/raw/<fuente>/` — nunca
sobrescribe corridas anteriores, así queda el histórico para análisis
longitudinal.

## Limitación conocida: sesgo de supervivencia

Product Hunt e Indie Hackers solo muestran a quien lanzó y (en el caso de
IH) reportó ingresos — quien fracasó y desapareció no está. Esto se declara
como limitación explícita del estudio, no se corrige por diseño (ver
decisión del 2026-09-02: "asumirlo y declararlo").

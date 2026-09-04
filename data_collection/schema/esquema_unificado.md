# Esquema unificado

Todas las fuentes convergen a esta tabla en `data/processed/`. La ingesta
cruda (`data/raw/`) conserva el formato nativo de cada API — la
normalización ocurre en un paso aparte (`scripts/normalize.py`, pendiente
de construir cuando haya volumen suficiente para justificarlo).

## Tabla: `entity`

| Campo | Tipo | Descripción |
|---|---|---|
| `entity_id` | string | `<fuente>:<id_nativo>` — llave única global |
| `source` | string | `producthunt` \| `reddit` \| `indiehackers` \| `flippa` \| ... |
| `source_native_id` | string | id tal como lo da la fuente |
| `entity_type` | string | `product` \| `post` \| `comment` \| `person` |
| `name_or_title` | string | |
| `description_text` | string | texto libre (tagline, body, selftext) |
| `url` | string | |
| `created_at` | datetime ISO8601 | |
| `retrieved_at` | datetime ISO8601 | cuándo se recolectó (no cuándo se creó) |
| `author_handle` | string \| null | username/maker, si es público |
| `maker_count` | int \| null | nº de fundadores/makers declarados |
| `metric_primary` | float \| null | votos / upvotes / score, según fuente |
| `metric_secondary` | float \| null | comentarios / respuestas |
| `revenue_signal` | float \| null | MRR/ingreso autoreportado, si existe |
| `category_raw` | string \| null | topic/categoría nativa de la fuente |
| `structural_signal` | bool \| null | ver definicion_operativa.md |
| `intentional_signal` | bool \| null | ídem |
| `leverage_signal` | bool \| null | ídem |
| `is_solopreneur_candidate` | bool \| null | ídem |
| `labeling_method` | string | versión de la heurística/clasificador usado |
| `raw_source_path` | string | ruta al JSON crudo del que proviene |

## Convenciones

- Nunca se transforma en el paso de ingesta más allá de aplanar campos
  anidados obvios — todo el crudo se conserva en `data/raw/` para
  reproducibilidad y auditoría.
- `entity_id` es la llave de unión entre capas (texto ↔ métricas ↔
  etiquetas manuales que se añadan después).
- Fechas siempre en UTC.

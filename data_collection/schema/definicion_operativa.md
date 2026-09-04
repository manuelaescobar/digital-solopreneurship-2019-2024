# Definición operativa de "solopreneur"

Tres criterios (decisión del 2026-09-02). El registro se etiqueta
`is_solopreneur_candidate = true` solo si hay evidencia a favor de los tres;
si falta evidencia para alguno, se marca `unknown`, no `false` por defecto.

1. **Estructural**: 0 empleados permanentes. Se toleran contratistas puntuales.
   - Señal en Product Hunt: `makers.length == 1` (proxy débil — un maker no
     implica 0 empleados, pero es lo único observable).
   - Señal en Reddit: autodeclaración en el post/comentario ("solo founder",
     "just me", "no employees").

2. **Intencional**: sin intención declarada de crecer vía nómina.
   - Señal: lenguaje en tagline/descripción/post ("bootstrapped", "staying
     small", "lifestyle business", "no VC").

3. **Apalancamiento**: ingresos desacoplados de horas trabajadas (producto,
   software, contenido, activo digital vs. venta de horas).
   - Señal: categoría/topic del producto (SaaS, herramienta, app, curso,
     newsletter de pago vs. "consulting", "agency services").

Este criterio 3 es el que distingue solopreneur de freelancer. Se registra
como campo separado (`leverage_signal`) para poder excluir freelancers puros
en el análisis, no en la recolección.

## Campos de etiquetado añadidos a cada registro crudo

- `structural_signal`: bool | null
- `intentional_signal`: bool | null
- `leverage_signal`: bool | null
- `is_solopreneur_candidate`: bool | null (true solo si los tres son true)
- `labeling_method`: "keyword_heuristic_v1" (por ahora; ver
  esquema_unificado.md para plan de mejora con clasificador)

La heurística por palabras clave (v1) es deliberadamente conservadora y
ruidosa — el objetivo de esta primera pasada es maximizar recall (no perder
candidatos), no precisión. La depuración fina se hace en la etapa de
`data/processed/`, no en la ingesta.

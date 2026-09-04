#!/usr/bin/env python3
"""
Procesa el Stack Overflow Developer Survey (CSV publico) y filtra la
subpoblacion de developer-solopreneurs: autoempleados con ingresos y
sin intencion declarada de contratar (heuristica sobre las columnas
disponibles, ver schema/definicion_operativa.md).

Paso manual previo (no automatizable: el sitio es una SPA sin link de
descarga directo en el HTML):
  1. Entra a https://survey.stackoverflow.co/<anio> (ej. 2024)
  2. Busca el boton "Download the dataset" / "Download CSV" (no requiere
     login ni registro)
  3. Descomprime el zip y ubica el archivo principal, tipicamente
     "survey_results_public.csv"
  4. Pasa esa ruta a este script con --input

Uso:
    python3 so_survey_process.py --input ~/Downloads/survey_results_public.csv --year 2024
"""
import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Nombres de columna conocidos por anio de encuesta (varian ligeramente).
# Se intenta cada alias en orden hasta encontrar uno presente en el CSV.
COLUMN_ALIASES = {
    "employment": ["Employment", "MainBranch", "EmploymentStatus"],
    "income": ["ConvertedCompYearly", "ConvertedComp", "CompTotal", "Salary"],
    "country": ["Country"],
    "years_pro": ["YearsCodePro", "YearsCodedJob"],
    "org_size": ["OrgSize", "CompanySize"],
    "dev_type": ["DevType", "DeveloperType"],
    "resp_id": ["ResponseId", "Respondent"],
}

# Anios cuya encuesta no ofrecia una categoria "Just me" en org_size (el
# bucket mas fino era "Fewer than 10 employees") -> el structural_signal
# para esos anios es necesariamente mas grueso (False cubre 1-9 empleados
# tambien, no solo 0). Se marca para no comparar prevalencia entre anios
# sin esta salvedad.
YEARS_WITHOUT_JUST_ME_CATEGORY = {2017, 2018}


def resolve_columns(fieldnames):
    resolved = {}
    lower_map = {f.lower(): f for f in fieldnames}
    for key, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias.lower() in lower_map:
                resolved[key] = lower_map[alias.lower()]
                break
    return resolved


def label_record(row, cols, year):
    org_size = (row.get(cols.get("org_size", ""), "") or "").lower().strip()

    # OrgSize es la unica senal estructural real disponible (0 empleados).
    # El campo Employment ya se uso para filtrar la fila (self-employed/
    # freelancer) y NO aporta informacion adicional sobre tamano de equipo -
    # usarlo aqui haria a casi todas las filas "candidatas" por definicion,
    # incluyendo a quien dirige una agencia de 50 personas.
    if "just me" in org_size:
        structural = True
    elif org_size in ("", "na", "i don’t know", "i don't know"):
        structural = None  # desconocido, no se asume False
    else:
        structural = False  # declaro un tamano de organizacion con mas gente

    intentional = None  # no hay columna directa; se deja para enriquecimiento posterior
    leverage = None
    # Sin senales de intencion/apalancamiento, el candidato se basa solo en
    # la senal estructural disponible (ver schema/definicion_operativa.md:
    # "unknown" se mantiene como None, nunca se fuerza a False).
    is_candidate = structural if structural is not None else None

    return {
        "structural_signal": structural,
        "intentional_signal": intentional,
        "leverage_signal": leverage,
        "is_solopreneur_candidate": is_candidate,
        "labeling_method": "keyword_heuristic_v1_so_survey",
        "org_size_granularity": "coarse_no_just_me_option" if year in YEARS_WITHOUT_JUST_ME_CATEGORY else "fine",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="ruta al CSV descargado")
    parser.add_argument("--year", type=int, required=True)
    args = parser.parse_args()

    input_path = Path(args.input).expanduser()
    if not input_path.exists():
        raise SystemExit(f"ERROR: no existe {input_path}")

    now = datetime.now(timezone.utc).isoformat()
    records = []

    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = resolve_columns(reader.fieldnames)
        missing = [k for k in ("employment",) if k not in cols]
        if missing:
            raise SystemExit(
                f"ERROR: no se encontraron columnas esperadas ({missing}) en el CSV. "
                f"Columnas disponibles: {reader.fieldnames[:15]}..."
            )

        for row in reader:
            employment = (row.get(cols.get("employment", ""), "") or "").lower()
            if "self-employed" not in employment and "freelancer" not in employment:
                continue  # nos quedamos solo con la subpoblacion relevante

            labels = label_record(row, cols, args.year)
            resp_id = row.get(cols.get("resp_id", ""), "")
            records.append({
                "entity_id": f"so_survey_{args.year}:{resp_id}",
                "source": "stackoverflow_survey",
                "source_native_id": resp_id,
                "entity_type": "person",
                "name_or_title": None,
                "description_text": None,
                "url": None,
                "created_at": f"{args.year}-01-01",
                "retrieved_at": now,
                "country": row.get(cols.get("country", "")),
                "years_experience_pro": row.get(cols.get("years_pro", "")),
                "org_size_raw": row.get(cols.get("org_size", "")),
                "dev_type_raw": row.get(cols.get("dev_type", "")),
                "metric_primary": row.get(cols.get("income", "")),
                "survey_year": args.year,
                **labels,
            })

    candidates = sum(1 for r in records if r["is_solopreneur_candidate"])
    print(f"Filas self-employed/freelancer encontradas: {len(records)}")
    print(f"Candidatos solopreneur (org_size == 'just me'): {candidates}")

    out_dir = ROOT / "data" / "raw" / "stackoverflow_survey"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"so_survey_{args.year}.json"
    out_path.write_text(json.dumps(records, indent=2, ensure_ascii=False))
    print(f"Guardado en: {out_path}")


if __name__ == "__main__":
    main()

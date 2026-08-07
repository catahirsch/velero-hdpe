"""Regenera el ranking del concurso.

    python3 -m concurso.leaderboard   ->  concurso/leaderboard.json

Junta todas las tarjetas de concurso/resultados/*/resultado.json, ordena por
puntaje automatico y escribe el JSON que consume la pagina del concurso.
El puntaje de jurado (hasta 40 pts) se carga a mano en cada tarjeta como
"jurado": {"total": X, "nota": "..."} cuando exista.
"""

from __future__ import annotations

import glob
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))


def main() -> None:
    filas = []
    for path in sorted(glob.glob(os.path.join(BASE, "resultados", "*", "resultado.json"))):
        with open(path) as f:
            r = json.load(f)
        if not r.get("valido"):
            continue
        jurado = r.get("jurado", {}).get("total")
        filas.append({
            "equipo": r["equipo"],
            "categoria": r.get("categoria", ""),
            "comentario": r.get("comentario", ""),
            "total_auto": r["total_auto"],
            "jurado": jurado,
            "total": round(r["total_auto"] + (jurado or 0), 1),
            "recuperacion": r["metricas"]["limite_recuperacion_deg"],
            "francobordo": r["metricas"]["francobordo_piso_carga_mm"],
            "sa_d": r["metricas"]["sa_d_carga"],
            "lastre_pct": r["metricas"]["relacion_lastre_pct"],
            "violaciones": len(r["metricas"]["violaciones_sobre"]),
            "gz": f"resultados/{r['equipo']}/gz.png",
        })
    filas.sort(key=lambda x: -x["total"])
    out = {"actualizado": None, "filas": filas}
    path = os.path.join(BASE, "leaderboard.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(f"escrito: {path} ({len(filas)} equipos)")


if __name__ == "__main__":
    main()

from __future__ import annotations

import re
from typing import Dict, List, Tuple
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError, available_timezones

from fastapi import HTTPException, status

try:  # pragma: no cover - fallback optional
    import pytz  # type: ignore
except Exception:  # pragma: no cover
    pytz = None  # type: ignore


HORARIO_REGEX = re.compile(r"^([01]\d|2[0-3]):[0-5]\d-([01]\d|2[0-3]):[0-5]\d$")
DIAS_VALIDOS = [
    "lunes",
    "martes",
    "miercoles",
    "jueves",
    "viernes",
    "sabado",
    "domingo",
]

COMMON_TZ_FALLBACK = {
    "UTC",
    "Etc/UTC",
    "America/Bogota",
    "America/Lima",
    "America/Mexico_City",
    "America/Santiago",
    "America/New_York",
    "Europe/Madrid",
}


def _to_minutes(hora: str) -> int:
    horas, minutos = hora.split(":")
    return int(horas) * 60 + int(minutos)


def _add_error(
    errores: list[dict], dia: str, detalle: str, code: str
) -> None:
    errores.append({"dia": dia, "detalle": detalle, "code": code})


def _is_valid_timezone(zona_horaria: str) -> bool:
    try:
        if available_timezones():
            return zona_horaria in available_timezones()
        ZoneInfo(zona_horaria)
        return True
    except ZoneInfoNotFoundError:
        pass
    except Exception:
        pass

    if pytz and zona_horaria in getattr(pytz, "all_timezones_set", set()):
        return True

    return zona_horaria in COMMON_TZ_FALLBACK


def collect_horario_errors(
    zona_horaria: str, horario_apertura_json: Dict[str, List[str]]
) -> list[dict]:
    errores: list[dict] = []

    # Validar zona horaria
    if not _is_valid_timezone(zona_horaria):
        _add_error(
            errores,
            "zona_horaria",
            f"Zona horaria invalida: {zona_horaria}",
            "ZONA_HORARIA_INVALIDA",
        )
        return errores

    if horario_apertura_json is None or not isinstance(horario_apertura_json, dict):
        _add_error(
            errores,
            "estructura",
            "horario_apertura_json debe ser un objeto con dias como claves",
            "FORMATO_HORARIO_INVALIDO",
        )
        return errores

    for dia, rangos in horario_apertura_json.items():
        if dia not in DIAS_VALIDOS:
            _add_error(
                errores,
                dia,
                f"Dia invalido: {dia}. Debe ser uno de {', '.join(DIAS_VALIDOS)}",
                "DIA_INVALIDO",
            )
            continue

        if not isinstance(rangos, list):
            _add_error(
                errores,
                dia,
                "Los rangos deben ser una lista de strings HH:MM-HH:MM",
                "FORMATO_HORARIO_INVALIDO",
            )
            continue

        rangos_validos: List[Tuple[int, int, str]] = []
        for rango in rangos:
            if not isinstance(rango, str) or not HORARIO_REGEX.match(rango):
                _add_error(
                    errores,
                    dia,
                    f"Formato invalido: '{rango}'. Esperado HH:MM-HH:MM",
                    "FORMATO_HORARIO_INVALIDO",
                )
                continue

            inicio_str, fin_str = rango.split("-")
            inicio_min = _to_minutes(inicio_str)
            fin_min = _to_minutes(fin_str)

            if inicio_min >= fin_min:
                _add_error(
                    errores,
                    dia,
                    f"Rango invertido o cruza medianoche: {rango}. Desdobla el tramo en dos dias.",
                    "RANGO_INVALIDO",
                )
                continue

            rangos_validos.append((inicio_min, fin_min, rango))

        # Validar solapes solo con rangos validos
        rangos_validos.sort(key=lambda x: x[0])
        for idx in range(1, len(rangos_validos)):
            prev_inicio, prev_fin, prev_txt = rangos_validos[idx - 1]
            inicio, fin, actual_txt = rangos_validos[idx]
            if inicio < prev_fin:
                _add_error(
                    errores,
                    dia,
                    f"Solape entre {prev_txt} y {actual_txt}",
                    "SOLAPE_HORARIO",
                )

    return errores


def ensure_horario_valido(
    zona_horaria: str, horario_apertura_json: Dict[str, List[str]]
) -> None:
    errores = collect_horario_errors(zona_horaria, horario_apertura_json)
    if errores:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "HORARIO_INVALIDO",
                    "message": "Horario invalido",
                    "errores": errores,
                    "zona_horaria": zona_horaria,
                }
            },
        )

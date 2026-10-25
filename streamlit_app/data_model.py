"""Transforma cada lançamento em linhas individuais e totais de ocorrência.

Regra: a planilha armazena um lançamento por linha. O dashboard expande esse lançamento
para cada policial/tipo, mas os gráficos agregam o tipo de ocorrência apenas uma vez
por lançamento, independentemente da quantidade de integrantes da equipe.
"""
from __future__ import annotations

import re
from datetime import date
from typing import Any

import pandas as pd

from scoring import PTS_BASE, ammo_tier, calculate_points, is_entorpecente, is_municao
ROLES = ["Cmt", "Mot", "P1", "P2"]


def to_int(value: Any, default: int = 1) -> int:
    try:
        text = str(value or "").strip().replace(",", ".")
        n = int(float(text))
        return max(1, n)
    except (ValueError, TypeError, OverflowError):
        return default


def to_date(value: Any) -> date | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        # Trata explicitamente ISO para evitar ambiguidade dia/mês; aceita também dd/mm/aaaa.
        text = str(value).strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            return date.fromisoformat(text)
        parsed = pd.to_datetime(text, errors="coerce", dayfirst=True)
        return None if pd.isna(parsed) else parsed.date()
    except Exception:
        return None


def sorted_numbered_values(row: dict[str, Any], prefix: str) -> list[str]:
    matches: list[tuple[int, str]] = []
    pattern = re.compile(rf"{re.escape(prefix)}\s*(\d+)$", re.I)
    for key, value in row.items():
        match = pattern.fullmatch(str(key).strip())
        if match and str(value or "").strip():
            matches.append((int(match.group(1)), str(value).strip()))
    return [value for _, value in sorted(matches)]


def get_members(row: dict[str, Any]) -> list[str]:
    teams: dict[int, dict[str, str]] = {}
    for key, value in row.items():
        match = re.fullmatch(r"Equipe\s+(\d+)\s+-\s+(Cmt|Mot|P1|P2)", str(key).strip(), re.I)
        if not match or not str(value or "").strip():
            continue
        team_idx, role = int(match.group(1)), match.group(2).title()
        teams.setdefault(team_idx, {})[role] = str(value).strip()
    result: list[str] = []
    seen: set[str] = set()
    for team_idx in sorted(teams):
        for role in ROLES:
            value = teams[team_idx].get(role, "").strip()
            normalized = " ".join(value.casefold().split())
            if value and normalized not in seen:
                result.append(value)
                seen.add(normalized)
    return result


def score_launch_types(row: dict[str, Any], point_map: dict[str, float]) -> list[dict[str, Any]]:
    selected = sorted_numbered_values(row, "Tipo OC ")
    quantity = to_int(row.get("Quantidade informada"), 1)
    ammo_qty = to_int(row.get("Quantidade de munições"), 1)
    resolved: list[dict[str, Any]] = []
    seen: set[str] = set()
    scoring_map = {**PTS_BASE, **point_map}
    for kind in selected:
        effective_type = ammo_tier(ammo_qty) if is_municao(kind) else kind
        norm = effective_type.casefold()
        if norm in seen:
            continue
        seen.add(norm)
        if is_entorpecente(effective_type) or is_municao(effective_type):
            individual_qty = 1
            points = int(round(float(scoring_map.get(effective_type, 0))))
        else:
            individual_qty = quantity
            points = int(calculate_points(effective_type, quantity, point_map))
        resolved.append({"tipo_oc": effective_type, "qtde_individual": individual_qty, "pontos": points})
    return resolved


def build_frames(launch_rows: list[dict[str, Any]], point_map: dict[str, float]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    details: list[dict[str, Any]] = []
    facts: list[dict[str, Any]] = []
    launch_meta: list[dict[str, Any]] = []
    for row in launch_rows:
        launch_id = str(row.get("ID", "")).strip()
        if not launch_id:
            continue
        launch_date = to_date(row.get("Data"))
        company = str(row.get("Companhia", "")).strip()
        subdivision = str(row.get("Subdivisão", "")).strip()
        members = get_members(row)
        types = score_launch_types(row, point_map)
        launch_meta.append({
            "ID": launch_id,
            "Data": launch_date,
            "Companhia": company,
            "Subdivisão": subdivision,
            "Integrantes": members,
            "Tipos": [item["tipo_oc"] for item in types],
            "_row_number": row.get("_row_number"),
        })
        for item in types:
            facts.append({
                "ID": launch_id,
                "Data": launch_date,
                "Companhia": company,
                "Subdivisão": subdivision,
                "Tipo de OC": item["tipo_oc"],
                "Qtde": 1,  # Uma ocorrência do tipo no lançamento, não uma por policial.
                "Pontos": item["pontos"],
            })
            for member in members:
                details.append({
                    "ID": launch_id,
                    "Data": launch_date,
                    "Companhia": company,
                    "Subdivisão": subdivision,
                    "Efetivo": member,
                    "Tipo de OC": item["tipo_oc"],
                    "Qtde": item["qtde_individual"],
                    "Pontos": item["pontos"],
                })
    detail_cols = ["ID", "Data", "Companhia", "Subdivisão", "Efetivo", "Tipo de OC", "Qtde", "Pontos"]
    fact_cols = ["ID", "Data", "Companhia", "Subdivisão", "Tipo de OC", "Qtde", "Pontos"]
    meta_cols = ["ID", "Data", "Companhia", "Subdivisão", "Integrantes", "Tipos", "_row_number"]
    details_df = pd.DataFrame(details, columns=detail_cols)
    facts_df = pd.DataFrame(facts, columns=fact_cols)
    meta_df = pd.DataFrame(launch_meta, columns=meta_cols)
    return details_df, facts_df, meta_df


def totals_by_dimension(facts: pd.DataFrame, dimension: str) -> pd.DataFrame:
    cols = [dimension, "Qtde", "Pontos"]
    if facts.empty or dimension not in facts.columns:
        return pd.DataFrame(columns=cols + ["Porcentagem de Ocorrências", "Porcentagem de Pontos"])
    result = facts.groupby(dimension, dropna=False).agg(Qtde=("Qtde", "sum"), Pontos=("Pontos", "sum")).reset_index()
    total_qty = float(result["Qtde"].sum()) or 1.0
    total_points = float(result["Pontos"].sum()) or 1.0
    result["Porcentagem de Ocorrências"] = result["Qtde"] / total_qty * 100
    result["Porcentagem de Pontos"] = result["Pontos"] / total_points * 100
    result = result.sort_values(["Qtde", "Pontos"], ascending=False).reset_index(drop=True)
    return result


def ranking_frame(details: pd.DataFrame) -> pd.DataFrame:
    columns = ["Efetivo", "Companhia", "Subdivisão", "Qtde", "Pontos"]
    if details.empty:
        return pd.DataFrame(columns=columns)
    result = details.groupby(["Efetivo", "Companhia", "Subdivisão"], dropna=False).agg(Qtde=("Qtde", "sum"), Pontos=("Pontos", "sum")).reset_index()
    result["Pontos"] = pd.to_numeric(result["Pontos"], errors="coerce").fillna(0)
    result["Qtde"] = pd.to_numeric(result["Qtde"], errors="coerce").fillna(0)
    return result.sort_values(["Pontos", "Qtde", "Efetivo"], ascending=[False, False, True]).reset_index(drop=True)

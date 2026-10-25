"""Organograma oficial de Companhias e Subdivisões do 15º BPM/PMRN."""
from __future__ import annotations

import re
import unicodedata

COMPANHIAS: dict[str, list[str]] = {
    "1ª CPM/Sede Santa Cruz": [
        "1º Pelotão — Santa Cruz",
        "DPM de Campo Redondo",
        "DPM de Lajes Pintadas",
    ],
    "2ª CPM/Sede Tangará": [
        "1º Pelotão — Tangará",
        "DPM de Sítio Novo",
        "DPM de Serra Caiada",
        "DPM de Boa Saúde",
        "DPM de Sen. Elói de Souza",
    ],
    "3ª CPM/Sede Santa Cruz": [
        "1º Pelotão — Jaçanã",
        "DPM de Cel. Ezequiel",
        "DPM de Japi",
        "DPM de São Bento do Trairi",
    ],
}


def normalize_org_label(value: object) -> str:
    """Normaliza espaços, equivalência de grau/ordinal e acentos Unicode sem alterar rótulos exibidos."""
    text = unicodedata.normalize("NFKC", str(value or "").replace("°", "º"))
    text = re.sub(r"\s+", " ", text).strip()
    return text.casefold()


def subdivisions_for(company: str) -> list[str]:
    """Retorna exclusivamente as subdivisões vinculadas à Companhia indicada."""
    return list(COMPANHIAS.get(company, []))


def subdivision_belongs_to(company: str, subdivision: str) -> bool:
    """Confirma a relação hierárquica Companhia -> Subdivisão, tolerando caixa/espaços."""
    company_key = next((k for k in COMPANHIAS if normalize_org_label(k) == normalize_org_label(company)), None)
    if not company_key:
        return False
    return any(normalize_org_label(d) == normalize_org_label(subdivision) for d in COMPANHIAS[company_key])

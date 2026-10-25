"""Regras de pontuação consolidadas da aplicação 15BPM_PMRN."""
from __future__ import annotations

OCORRENCIAS_BASE: list[tuple[str, int]] = [
    ("ARMA BRANCA (Homicídio, Tentativa de homicídio com Lesão Corporal Grave e Roubo consumado)", 5),
    ("ARTESANAL CURTA", 20),
    ("ARTESANAL LONGA", 25),
    ("COLETE BALÍSTICO", 20),
    ("ESPINGARDA", 35),
    ("METRALHADORA", 80),
    ("FUZIL", 100),
    ("PISTOLA", 40),
    ("REVÓLVER", 30),
    ("RIFLE", 35),
    ("SIMULACRO", 6),
    ("ENTORPECENTE De 1g a 500g - Peso 1 (Duas ou mais Ocorrências no mesmo dia até o total contará como pontuação subsequente)", 15),
    ("ENTORPECENTE De 500g a 2kg - Peso 2 (Duas ou mais Ocorrências no mesmo dia até o total contará como pontuação subsequente)", 20),
    ("ENTORPECENTE De 2kg a 10kg - Peso 3 (Duas ou mais Ocorrências no mesmo dia até o total contará como pontuação subsequente)", 30),
    ("ENTORPECENTE Acima de 10kg - Peso 4", 50),
    ("ARROMBAMENTO", 6),
    ("ESTELIONATO", 7),
    ("FURTO", 6),
    ("RECEPTAÇÃO", 8),
    ("ROUBO", 12),
    ("MUNIÇÃO 1 - 10", 5),
    ("MUNIÇÃO 11 - 20", 10),
    ("MUNIÇÃO 21 - 50", 15),
    ("MUNIÇÃO 51 - 100", 20),
    ("MUNIÇÃO 101 ou mais", 30),
    ("FORAGIDO", 10),
    ("VEÍCULO ABANDONADO", 6),
    ("VEÍCULO (FURTO/ROUBO) APREENDIDO (Apenas veículos com queixa de furto/roubo/adulterado ou usados para crimes como: Homicídios, roubos e transportes de entorpecentes)", 7),
    ("TCO/BOC 4º BPM", 6),
    ("TCO/BOC DELEGACIA", 3),
    ("BOPPM (Oc's como: Isolamento local de crime, ameaça, perturbação sossego alheio, etc..)", 3),
    ("VIOLÊNCIA DOMÉSTICA", 5),
    ("ESTUPRO (Com flagrante, vítima, acusado e materialidade)", 30),
    ("HOMICÍDIO COM PRISÃO EM FLAGRANTE (Apenas para homicídios consumados)", 50),
]
PTS_BASE: dict[str, int] = dict(OCORRENCIAS_BASE)


def is_municao(tipo: str) -> bool:
    normalized = str(tipo or "").strip().upper()
    return normalized.startswith("MUNIÇÃO") or normalized.startswith("MUNICAO")


def is_entorpecente(tipo: str) -> bool:
    return str(tipo or "").strip().upper().startswith("ENTORPECENTE")


def ammo_tier(quantity: int) -> str:
    count = max(1, int(quantity))
    if count <= 10:
        return "MUNIÇÃO 1 - 10"
    if count <= 20:
        return "MUNIÇÃO 11 - 20"
    if count <= 50:
        return "MUNIÇÃO 21 - 50"
    if count <= 100:
        return "MUNIÇÃO 51 - 100"
    return "MUNIÇÃO 101 ou mais"


def calculate_points(tipo: str, quantity: int, point_map: dict[str, float] | None = None) -> int:
    # As regras conhecidas e testadas da aplicação original têm precedência;
    # point_map complementa apenas tipos adicionais que existam no banco.
    points = {**(point_map or {}), **PTS_BASE}
    if is_entorpecente(tipo):
        return int(round(float(points.get(tipo, 0))))
    if is_municao(tipo):
        tier = ammo_tier(quantity)
        return int(round(float(points.get(tier, 0))))
    return int(round(max(1, int(quantity)) * float(points.get(tipo, 0))))

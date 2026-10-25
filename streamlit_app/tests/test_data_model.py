import pandas as pd

from data_model import build_frames, percentage_of_total_points, ranking_frame
from scoring import PTS_BASE


def test_team_members_are_expanded_for_individual_ranking_but_not_company_totals():
    record = {
        "ID": "oc-001",
        "Data": "2026-10-21",
        "Companhia": "3ª CPM/Sede Santa Cruz",
        "Subdivisão": "DPM de Cel. Ezequiel",
        "Quantidade informada": "1",
        "Quantidade de munições": "1",
        "Equipe 1 - Cmt": "2º SGT PM RICARDO",
        "Equipe 1 - Mot": "3º SGT PM VALCÁCIO",
        "Equipe 1 - P1": "CB PM LUNA",
        "Equipe 1 - P2": "SD PM PASTEL",
        "Tipo OC 1": "FUZIL",
    }
    details, facts, _ = build_frames([record], PTS_BASE)
    assert len(details) == 4
    assert int(details["Qtde"].sum()) == 4
    assert float(details["Pontos"].sum()) == 400.0
    assert len(facts) == 1
    assert int(facts["Qtde"].sum()) == 1
    assert float(facts["Pontos"].sum()) == 100.0
    assert len(ranking_frame(details)) == 4


def test_multiple_types_share_one_sheet_row_and_each_type_counts_once_in_distribution():
    record = {
        "ID": "oc-002",
        "Data": "21/10/2026",
        "Companhia": "2ª CPM/Sede Tangará",
        "Subdivisão": "DPM de Sítio Novo",
        "Quantidade informada": "2",
        "Quantidade de munições": "30",
        "Equipe 1 - Cmt": "1º SGT PM SAMUEL",
        "Equipe 1 - Mot": "CB PM LUNA",
        "Tipo OC 1": "FURTO",
        "Tipo OC 2": "MUNIÇÃO 1 - 10",
    }
    details, facts, _ = build_frames([record], PTS_BASE)
    assert len(details) == 4  # 2 integrantes x 2 tipos de OC
    assert int(facts["Qtde"].sum()) == 2  # uma unidade por tipo lançado, não por integrante
    # FURTO: 2 x 6 pontos; munição de 30 unidades: faixa 21-50 = 15 pontos.
    assert float(facts["Pontos"].sum()) == 27.0
    assert float(details["Pontos"].sum()) == 54.0


def test_duplicate_person_within_same_launch_is_counted_once():
    record = {
        "ID": "oc-003",
        "Data": "2026-10-21",
        "Companhia": "1ª CPM/Sede Santa Cruz",
        "Subdivisão": "1º Pelotão — Santa Cruz",
        "Quantidade informada": "1",
        "Quantidade de munições": "1",
        "Equipe 1 - Cmt": "CB PM LUNA",
        "Equipe 1 - Mot": "CB PM LUNA",
        "Equipe 1 - P1": "SD PM PASTEL",
        "Tipo OC 1": "FURTO",
    }
    details, facts, _ = build_frames([record], PTS_BASE)
    assert len(details) == 2
    assert int(facts["Qtde"].sum()) == 1


def test_points_are_integer_values_for_occurrence_and_individual_frames():
    record = {
        "ID": "oc-int-001",
        "Data": "2026-10-21",
        "Companhia": "1ª CPM/Sede Santa Cruz",
        "Subdivisão": "DPM de Campo Redondo",
        "Quantidade informada": "2",
        "Equipe 1 - Cmt": "SD PM JOÃO DA SILVA",
        "Tipo OC 1": "FURTO",
    }
    details, facts, _ = build_frames([record], PTS_BASE)
    assert int(details.loc[0, "Pontos"]) == 12
    assert int(facts.loc[0, "Pontos"]) == 12
    assert float(details.loc[0, "Pontos"]).is_integer()
    assert float(facts.loc[0, "Pontos"]).is_integer()


def test_ranking_accumulates_points_for_same_person_across_companies():
    details = pd.DataFrame(
        [
            {
                "Efetivo": "CB PM LUNA",
                "Companhia": "1ª CPM",
                "Subdivisão": "DPM A",
                "Qtde": 2,
                "Pontos": 12,
            },
            {
                "Efetivo": "CB PM LUNA",
                "Companhia": "2ª CPM",
                "Subdivisão": "DPM B",
                "Qtde": 1,
                "Pontos": 15,
            },
        ]
    )

    ranking = ranking_frame(details)

    assert len(ranking) == 1
    assert ranking.loc[0, "Efetivo"] == "CB PM LUNA"
    assert ranking.loc[0, "Qtde"] == 3
    assert ranking.loc[0, "Pontos"] == 27
    assert ranking.loc[0, "Companhia"] == "Várias"
    assert ranking.loc[0, "Subdivisão"] == "Várias"


def test_percentage_of_total_points_uses_filtered_points_as_numerator():
    all_facts = pd.DataFrame({"Pontos": [10, 30]})
    filtered_facts = pd.DataFrame({"Pontos": [10]})

    assert percentage_of_total_points(filtered_facts, all_facts) == 25


def test_date_range_filters_details_and_facts_inclusively():
    from datetime import date

    from app import apply_filters

    dates = [date(2026, 10, 1), date(2026, 10, 10), date(2026, 10, 31), date(2026, 11, 1)]
    details = pd.DataFrame(
        {
            "ID": ["before", "start", "end", "after"],
            "Data": dates,
            "Companhia": ["C"] * 4,
            "Subdivisão": ["D"] * 4,
            "Tipo de OC": ["FURTO"] * 4,
            "Efetivo": ["POLICIAL"] * 4,
        }
    )
    facts = details.drop(columns="Efetivo")
    filters = {
        "start_date": date(2026, 10, 10),
        "end_date": date(2026, 10, 31),
        "company": "Todos",
        "division": "Todos",
        "types": [],
        "people": [],
    }

    filtered_details, filtered_facts = apply_filters(details, facts, filters)

    assert filtered_details["ID"].tolist() == ["start", "end"]
    assert filtered_facts["ID"].tolist() == ["start", "end"]

from organization import COMPANHIAS, normalize_org_label, subdivision_belongs_to, subdivisions_for


def test_org_chart_has_exact_company_subdivision_mapping():
    assert subdivisions_for("1ª CPM/Sede Santa Cruz") == [
        "1º Pelotão — Santa Cruz", "DPM de Campo Redondo", "DPM de Lajes Pintadas"
    ]
    assert subdivisions_for("2ª CPM/Sede Tangará") == [
        "1º Pelotão — Tangará", "DPM de Sítio Novo", "DPM de Serra Caiada",
        "DPM de Boa Saúde", "DPM de Sen. Elói de Souza"
    ]
    assert subdivisions_for("3ª CPM/Sede Santa Cruz") == [
        "1º Pelotão — Jaçanã", "DPM de Cel. Ezequiel", "DPM de Japi", "DPM de São Bento do Trairi"
    ]
    assert sum(map(len, COMPANHIAS.values())) == 12


def test_subdivision_must_belong_to_selected_company():
    assert subdivision_belongs_to("2ª CPM/Sede Tangará", "DPM de Sítio Novo")
    assert not subdivision_belongs_to("1ª CPM/Sede Santa Cruz", "DPM de Sítio Novo")
    assert not subdivision_belongs_to("Companhia desconhecida", "DPM de Sítio Novo")


def test_org_label_normalization_handles_case_and_extra_spaces():
    assert normalize_org_label("  DPM   DE   SÍTIO NOVO ") == normalize_org_label("DPM de Sítio Novo")
    assert normalize_org_label("1° Pelotão - Santa Cruz") == normalize_org_label("1º Pelotão - Santa Cruz")

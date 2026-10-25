from text_utils import normalize_person_name


def test_name_normalization_uppercases_and_preserves_spaces_between_names():
    assert normalize_person_name("  João   da Silva  ") == "JOÃO DA SILVA"


def test_name_normalization_preserves_hyphens_apostrophes_and_accents():
    assert normalize_person_name("Valcácio D'Ávila-Santos") == "VALCÁCIO D'ÁVILA-SANTOS"


def test_name_normalization_accepts_empty_value():
    assert normalize_person_name("   ") == ""

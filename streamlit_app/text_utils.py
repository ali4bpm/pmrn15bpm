"""Utilitários de normalização textual usados pelos formulários do 15BPM_PMRN."""
from __future__ import annotations

import re
import unicodedata


def normalize_person_name(value: object) -> str:
    """Converte nome de guerra para maiúsculas e reduz espaços repetidos sem os remover.

    Acentos, hífens, apóstrofos e espaços entre partes do nome são preservados.
    """
    text = unicodedata.normalize("NFC", str(value or "")).replace("°", "º")
    return re.sub(r"\s+", " ", text).strip().upper()

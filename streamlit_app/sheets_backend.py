"""Acesso e persistência no Google Sheets para o 15BPM_PMRN."""
from __future__ import annotations

import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import gspread
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
DEFAULT_SERVICE_ACCOUNT = APP_DIR / ".streamlit" / "google-service-account.json"
SPREADSHEET_ID_DEFAULT = "1fuZYlIANUvqA0PpIhVENef_b9DMIGFhd4R_9M2Atjao"
EMPLOYEE_TAB = "Efetivo 15BPM"
LAUNCH_TAB = "Lançamentos"
TYPES_TAB = "Tipos OC"
ROLES = ["Cmt", "Mot", "P1", "P2"]
BASE_LAUNCH_HEADERS = ["ID", "Data", "Companhia", "Subdivisão", "Quantidade informada", "Quantidade de munições", "Criado em"]
EMPLOYEE_HEADERS = ["ID", "Função", "Nome de Guerra", "Ativo", "Criado em"]
TYPE_HEADERS = ["ID", "Tipo de OC", "Pontos", "Ativo", "Criado em"]
DEFAULT_OCCURRENCE_HEADERS = [f"Tipo OC {i}" for i in range(1, 21)]


class SheetsSetupError(RuntimeError):
    """Configuração ausente ou acesso negado ao Google Sheets."""


def _config_value(section: str, name: str, env_name: str, default: str = "") -> str:
    value = os.getenv(env_name, "").strip()
    if value:
        return value
    try:
        value = str(st.secrets.get(section, {}).get(name, "")).strip()
        if value:
            return value
    except Exception:
        pass
    return default


def spreadsheet_id() -> str:
    return _config_value("google_sheets", "spreadsheet_id", "GOOGLE_SPREADSHEET_ID", SPREADSHEET_ID_DEFAULT)


def service_account_path() -> Path:
    value = _config_value("google_sheets", "service_account_file", "GOOGLE_SERVICE_ACCOUNT_FILE", str(DEFAULT_SERVICE_ACCOUNT))
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = (APP_DIR / path).resolve()
    return path


def create_spreadsheet_client() -> gspread.Spreadsheet:
    key_file = service_account_path()
    if not key_file.is_file():
        raise SheetsSetupError(
            "Não encontrei o arquivo de credenciais do Google. Salve o JSON da conta de serviço como "
            f"{DEFAULT_SERVICE_ACCOUNT.relative_to(APP_DIR).as_posix()} e siga o README."
        )
    try:
        gc = gspread.service_account(filename=str(key_file))
        return gc.open_by_key(spreadsheet_id())
    except Exception as exc:
        message = str(exc)
        if "403" in message or "permission" in message.lower() or "not have permission" in message.lower():
            raise SheetsSetupError(
                "O Google negou o acesso à planilha. Compartilhe a planilha com o e-mail client_email do JSON da conta de serviço, "
                "com permissão de Editor, e confirme que a API Google Sheets está habilitada."
            ) from exc
        if "404" in message or "not found" in message.lower():
            raise SheetsSetupError("Planilha não encontrada. Confira o ID em .streamlit/secrets.toml e a permissão da conta de serviço.") from exc
        raise SheetsSetupError(f"Falha ao conectar ao Google Sheets: {message}") from exc


def _worksheet(book: gspread.Spreadsheet, title: str, rows: int = 1000, cols: int = 40) -> gspread.Worksheet:
    try:
        return book.worksheet(title)
    except gspread.WorksheetNotFound:
        return book.add_worksheet(title=title, rows=rows, cols=cols)


def ensure_headers(ws: gspread.Worksheet, required: list[str]) -> list[str]:
    """Garante cabeçalhos sem apagar colunas nem registros já existentes."""
    existing = [str(v).strip() for v in ws.row_values(1)]
    if not existing or not any(existing):
        headers = list(required)
    else:
        headers = existing[:]
        # Corrige apenas cabeçalhos vazios intermediários, sem remover colunas existentes.
        for i, h in enumerate(headers):
            if not h:
                headers[i] = f"Coluna auxiliar {i + 1}"
        for name in required:
            if name not in headers:
                headers.append(name)
    if ws.col_count < len(headers):
        ws.resize(cols=len(headers))
    if headers != existing:
        ws.update([headers], "A1", value_input_option="RAW")
    return headers


def _default_launch_headers(max_teams: int = 10) -> list[str]:
    headers = list(BASE_LAUNCH_HEADERS)
    for i in range(1, max(1, max_teams) + 1):
        headers.extend([f"Equipe {i} - {role}" for role in ROLES])
    headers.extend(DEFAULT_OCCURRENCE_HEADERS)
    return headers


def initialize_schema(book: gspread.Spreadsheet, occurrence_base: list[tuple[str, float]]) -> dict[str, gspread.Worksheet]:
    """Cria abas necessárias e deixa a aba de efetivo como primeira, sem apagar abas antigas."""
    tabs = book.worksheets()
    tab_titles = [ws.title for ws in tabs]
    if EMPLOYEE_TAB not in tab_titles:
        # Renomeia uma guia padrão somente se estiver vazia; caso contrário preserva-a.
        if tabs and tabs[0].title.casefold() in {"sheet1", "planilha1", "página1", "pagina1", "folha1"} and not tabs[0].get_all_values():
            tabs[0].update_title(EMPLOYEE_TAB)
        else:
            book.add_worksheet(title=EMPLOYEE_TAB, rows=1000, cols=10, index=0)
    employees = _worksheet(book, EMPLOYEE_TAB, rows=1000, cols=10)
    launches = _worksheet(book, LAUNCH_TAB, rows=2000, cols=80)
    types = _worksheet(book, TYPES_TAB, rows=500, cols=10)

    ensure_headers(employees, EMPLOYEE_HEADERS)
    launch_headers = ensure_headers(launches, _default_launch_headers())
    ensure_headers(types, TYPE_HEADERS)

    # Semeia apenas tipos ausentes; não apaga nem sobrescreve ajustes existentes.
    existing_types = read_rows(types)
    current_names = {str(r.get("Tipo de OC", "")).strip().casefold() for r in existing_types}
    now = datetime.now().isoformat(timespec="seconds")
    headers_types = [str(v).strip() for v in types.row_values(1)]
    new_type_rows = []
    for name, points in occurrence_base:
        if name.casefold() not in current_names:
            mapping = {"ID": str(uuid.uuid4()), "Tipo de OC": name, "Pontos": points, "Ativo": True, "Criado em": now}
            new_type_rows.append([mapping.get(h, "") for h in headers_types])
    if new_type_rows:
        types.append_rows(new_type_rows, value_input_option="USER_ENTERED", insert_data_option="INSERT_ROWS")

    # Mantém abas da aplicação no início e preserva eventuais outras abas.
    tabs_now = book.worksheets()
    by_title = {ws.title: ws for ws in tabs_now}
    ordered = [by_title[EMPLOYEE_TAB], by_title[LAUNCH_TAB], by_title[TYPES_TAB]]
    ordered.extend(ws for ws in tabs_now if ws.title not in {EMPLOYEE_TAB, LAUNCH_TAB, TYPES_TAB})
    try:
        book.reorder_worksheets(ordered)
    except Exception:
        # Uma falha de ordenação não impede o uso dos dados.
        pass
    return {"employees": employees, "launches": launches, "types": types}


def read_rows(ws: gspread.Worksheet) -> list[dict[str, Any]]:
    values = ws.get_all_values()
    if not values:
        return []
    headers = [str(h).strip() for h in values[0]]
    if not any(headers):
        return []
    rows: list[dict[str, Any]] = []
    for row_number, cells in enumerate(values[1:], start=2):
        if not any(str(c).strip() for c in cells):
            continue
        item: dict[str, Any] = {}
        for i, header in enumerate(headers):
            if not header:
                continue
            item[header] = cells[i] if i < len(cells) else ""
        item["_row_number"] = row_number
        rows.append(item)
    return rows


def append_mapping(ws: gspread.Worksheet, mapping: dict[str, Any]) -> None:
    headers = [str(x).strip() for x in ws.row_values(1)]
    missing = [key for key in mapping if key not in headers]
    if missing:
        headers = ensure_headers(ws, headers + missing)
    vals = [mapping.get(h, "") for h in headers]
    ws.append_row(vals, value_input_option="RAW", insert_data_option="INSERT_ROWS")


def update_mapping(ws: gspread.Worksheet, row_number: int, mapping: dict[str, Any]) -> None:
    headers = [str(x).strip() for x in ws.row_values(1)]
    values = [mapping.get(h, "") for h in headers]
    if ws.col_count < len(values):
        ws.resize(cols=len(values))
    ws.update([values], f"A{row_number}", value_input_option="RAW")


def save_launch(ws: gspread.Worksheet, mapping: dict[str, Any], existing_row_number: int | None = None) -> None:
    current = [str(x).strip() for x in ws.row_values(1)]
    missing = [k for k in mapping if k not in current]
    if missing:
        current = ensure_headers(ws, current + missing)
    # Em uma edição, preserva colunas extras que o usuário tenha criado manualmente,
    # mas zera slots antigos de equipe/tipo que deixaram de ser usados no lançamento.
    if existing_row_number is not None:
        cells = ws.row_values(existing_row_number)
        previous = {h: cells[i] if i < len(cells) else "" for i, h in enumerate(current)}
        normalized: dict[str, Any] = {}
        for header in current:
            if header in mapping:
                normalized[header] = mapping[header]
            elif re.fullmatch(r"Equipe\s+\d+\s+-\s+(Cmt|Mot|P1|P2)", header, re.I) or re.fullmatch(r"Tipo OC\s*\d+", header, re.I):
                normalized[header] = ""
            else:
                normalized[header] = previous.get(header, "")
        update_mapping(ws, existing_row_number, normalized)
    else:
        normalized = {h: mapping.get(h, "") for h in current}
        append_mapping(ws, normalized)


def delete_launch(
    ws: gspread.Worksheet,
    existing_row_number: int,
) -> None:
    """Exclui um lançamento pela linha física da planilha."""

    row_number = int(existing_row_number)

    if row_number < 2:
        raise ValueError(
            "Linha inválida. Não é permitido excluir o cabeçalho da planilha."
        )

    ws.delete_rows(row_number)


def make_id() -> str:
    return str(uuid.uuid4())


def record_timestamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def is_active(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().casefold()
    if not text:
        return True
    return text in {"true", "sim", "1", "yes", "ativo"}


def record_row_number(rows: list[dict[str, Any]], record_id: str) -> int | None:
    for row in rows:
        if str(row.get("ID", "")) == str(record_id):
            return int(row.get("_row_number", 0)) or None
    return None


def launch_team_count(row: dict[str, Any] | None) -> int:
    if not row:
        return 1
    indexes = []
    for key, value in row.items():
        m = re.fullmatch(r"Equipe\s+(\d+)\s+-\s+(Cmt|Mot|P1|P2)", str(key), re.I)
        if m and str(value or "").strip():
            indexes.append(int(m.group(1)))
    return max(indexes, default=1)

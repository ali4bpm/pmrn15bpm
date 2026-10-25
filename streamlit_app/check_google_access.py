from __future__ import annotations

import json
from pathlib import Path

from sheets_backend import create_spreadsheet_client, service_account_path, spreadsheet_id


def main() -> int:
    key_path = service_account_path()
    if not key_path.is_file():
        print("ERRO: arquivo de credenciais nao encontrado:", key_path)
        print("Consulte o README.md para criar a conta de servico e colocar o JSON no local esperado.")
        return 1
    try:
        with key_path.open("r", encoding="utf-8") as f:
            info = json.load(f)
        print("Arquivo JSON reconhecido.")
        print("E-mail da conta de servico:", info.get("client_email", "nao informado"))
        book = create_spreadsheet_client()
        print("Conexao com Google Sheets: OK")
        print("Titulo da planilha:", book.title)
        print("Abas atuais:", ", ".join(ws.title for ws in book.worksheets()))
        print("ID configurado:", spreadsheet_id())
        return 0
    except Exception as exc:
        print("Falha na conexao:", exc)
        print("Verifique se a conta de servico foi compartilhada como Editor e se as APIs estao habilitadas.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

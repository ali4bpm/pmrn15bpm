from unittest.mock import Mock

import sheets_backend


def test_create_spreadsheet_client_uses_service_account_from_streamlit_secrets(monkeypatch):
    service_account_info = {
        "type": "service_account",
        "client_email": "15bpm-test@example.iam.gserviceaccount.com",
    }
    spreadsheet = Mock()
    client = Mock()
    client.open_by_key.return_value = spreadsheet
    monkeypatch.setattr(
        sheets_backend.st,
        "secrets",
        {
            "google_sheets": {
                "spreadsheet_id": "test-spreadsheet-id",
                "service_account": service_account_info,
            }
        },
    )
    monkeypatch.setattr(
        sheets_backend.gspread,
        "service_account_from_dict",
        Mock(return_value=client),
    )

    result = sheets_backend.create_spreadsheet_client()

    assert result is spreadsheet
    sheets_backend.gspread.service_account_from_dict.assert_called_once_with(
        service_account_info
    )
    client.open_by_key.assert_called_once_with("test-spreadsheet-id")

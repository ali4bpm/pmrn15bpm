import base64
import zlib

import pandas as pd

from app import pdf_report


def test_pdf_report_includes_institutional_title_and_filtered_indicators():
    pdf = pdf_report(
        pd.DataFrame([{"Efetivo": "POLICIAL", "Pontos": 42}]),
        "Resumo",
        "Teste",
        ["Efetivo", "Pontos"],
        {
            "Ocorrências": "3",
            "Ocorrências por tipo": "5",
            "Pontos das ocorrências": "42",
            "% Pontos": "25,0%",
        },
    )
    stream_start = pdf.index(b"stream\n") + len(b"stream\n")
    stream_end = pdf.index(b"endstream", stream_start)
    page_content = zlib.decompress(
        base64.a85decode(pdf[stream_start:stream_end], adobe=True)
    )

    assert pdf.startswith(b"%PDF-")
    assert b"(Produtividade e Pontua" in page_content
    assert b"15\\272 BPM PMRN)" in page_content
    assert b"OCORR\\312NCIAS)" in page_content
    assert b"OCORR\\312NCIAS POR TIPO)" in page_content
    assert b"PONTOS DAS OCORR\\312NCIAS)" in page_content
    assert b"% PONTOS)" in page_content
    assert b"(3) Tj" in page_content
    assert b"(5) Tj" in page_content
    assert b"(42) Tj" in page_content
    assert b"(25,0%) Tj" in page_content

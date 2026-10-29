from __future__ import annotations

import hmac
import io
import os
import re
import time
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from data_model import build_frames, percentage_of_total_points, ranking_frame, totals_by_dimension
from scoring import OCORRENCIAS_BASE, PTS_BASE
from sheets_backend import (
    EMPLOYEE_HEADERS, EMPLOYEE_TAB, LAUNCH_TAB, ROLES, TYPE_HEADERS, TYPES_TAB,
    SheetsSetupError, append_mapping, create_spreadsheet_client, initialize_schema,
    delete_launch, is_active, make_id, read_rows, record_timestamp, save_launch,
    spreadsheet_id, update_mapping,
)

APP_TITLE = "Produtividade e Pontuação — 15º BPM PMRN"
PAGE_TITLE = "15BPM_PMRN"
SESSION_HOURS = 8
APP_DIR = Path(__file__).resolve().parent
LOGO_PATH = APP_DIR / "assets" / "brasao_15bpm.png"
FAVICON_PATH = APP_DIR / "assets" / "favicon_15bpm.png"
FUNCOES = ["SD PM", "CB PM", "3º SGT PM", "2º SGT PM", "1º SGT PM", "ST PM", "ASP PM", "2º TEN PM", "1º TEN PM", "CAP PM", "MAJ PM", "TC PM", "CEL PM"]
from organization import COMPANHIAS, normalize_org_label
from text_utils import normalize_person_name

st.set_page_config(page_title=PAGE_TITLE, page_icon=str(FAVICON_PATH), layout="wide", initial_sidebar_state="auto")


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root { color-scheme: light; }
        .stApp { background: #f7f6f0; color: #202936; }
        [data-testid="stSidebar"] { background: #fffefd; border-right: 1px solid #d5d0c4; }
        .block-container { max-width: 1400px; padding: 1.25rem 1.5rem 2rem; }
        .main-title { text-align:center; color:#202936; font-weight:800; letter-spacing:-.025em; line-height:1.2; text-transform:uppercase; }
        .sidebar-title { text-align:center; color:#202936; font-weight:800; margin-top:.2rem; margin-bottom:.65rem; width:100%; text-transform:uppercase; }
        .app-footer { text-align:center !important; width:100%; color:#8b8f99; font-size:.82rem; padding:1.25rem .4rem .5rem; text-transform:uppercase; }
        /* Tipografia visual em maiúsculas em toda a aplicação; os valores persistidos
           continuam normalizados pela lógica de dados e preservam acentos UTF-8. */
        .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
        .stApp label, .stApp button, .stApp input, .stApp textarea, .stApp select,
        .stApp option, .stApp summary, .stApp li, .stApp [data-testid="stCaptionContainer"],
        .stApp [data-testid="stMetricLabel"], .stApp [data-testid="stMetricValue"],
        .stApp [data-testid="stAlertContent"], .stApp [data-testid="stWidgetLabel"] {
          text-transform:uppercase !important;
        }
        .stApp [data-testid="stMarkdownContainer"] *:not(svg):not(path):not(.material-symbols-rounded) {
          text-transform:uppercase !important;
        }
        .stApp h2, .stApp h3 { text-align:center !important; }
        .stApp [data-testid="stMultiSelect"] input { text-transform:uppercase !important; }
        .stApp [data-baseweb="popover"] *:not(svg):not(path):not(.material-symbols-rounded),
        .stApp [role="option"] { text-transform:uppercase !important; }
        [data-testid="stSidebar"] [data-testid="stImage"] {
          display:flex !important; flex-direction:column; align-items:center !important;
          justify-content:center !important; width:100% !important;
        }
        [data-testid="stSidebar"] [data-testid="stImage"] > div {
          display:flex !important; justify-content:center !important; align-items:center !important;
          margin-left:auto !important; margin-right:auto !important; max-width:100%;
        }
        [data-testid="stSidebar"] [data-testid="stImage"] img {
          display:block !important; margin-left:auto !important; margin-right:auto !important;
          object-fit:contain; max-width:100%; height:auto;
        }
        div[data-testid="stMetric"] { background:#fffefd; border:1px solid #d5d0c4; padding:12px 14px; border-radius:10px; }
        div[data-testid="stMetricLabel"] { font-size:.83rem; }
        div[data-testid="stMetricValue"] { font-variant-numeric:tabular-nums; }
        div.stButton > button[kind="primary"], div.stDownloadButton > button { background:#41439a; border-color:#41439a; color:white; }
        div.stButton > button { border-radius:8px; min-height:2.7rem; white-space:normal; line-height:1.25; }
        div.stButton > button[kind="primary"] { font-size:1rem; font-weight:700; }
        div[data-testid="stFormSubmitButton"] > button { min-height:2.7rem; white-space:normal; }
        h2, h3 { color:#202936; }
        div[data-testid="stDataFrame"] { max-width:100%; }
        [data-testid="stTabs"] button { min-height:2.8rem; font-weight:600; }
        #MainMenu, [data-testid="stStatusWidget"], .stAppDeployButton { display:none !important; }
        [data-testid="stSidebarCollapseButton"], [data-testid="stSidebarCollapsedControl"] {
          visibility:visible !important; opacity:1 !important; pointer-events:auto !important;
          z-index:1000 !important;
        }
        footer { visibility:hidden; }

        /* Layouts fluidos para tablets e telefones. As colunas passam a quebrar linhas,
           mantendo os campos de equipe legíveis em vez de espremer quatro seletores. */
        @media (max-width: 900px) {
          .block-container { padding: 1rem 1rem 1.5rem; }
          [data-testid="stHorizontalBlock"] { flex-wrap:wrap !important; gap:.65rem !important; }
          [data-testid="stHorizontalBlock"] > [data-testid="column"] {
            min-width: calc(50% - .4rem) !important;
            flex: 1 1 calc(50% - .4rem) !important;
          }
          [data-testid="stMetric"] { padding:10px !important; }
          [data-testid="stTabs"] [role="tablist"] { flex-wrap:wrap !important; gap:.3rem !important; }
          [data-testid="stTabs"] button { white-space:normal !important; height:auto !important; }
          [data-testid="stSidebar"] { min-width:0 !important; }
        }
        @media (max-width: 520px) {
          .block-container { padding: .75rem .65rem 1.25rem; }
          .main-title { font-size:1.55rem !important; }
          [data-testid="stHorizontalBlock"] > [data-testid="column"] {
            min-width:100% !important;
            flex:1 1 100% !important;
          }
          div[data-testid="stMetric"] { padding:9px !important; }
          div[data-testid="stMetricLabel"] { font-size:.78rem !important; }
          div[data-testid="stMetricValue"] { font-size:1.45rem !important; }
          [data-testid="stTabs"] [role="tablist"] { flex-direction:column !important; align-items:stretch !important; }
          [data-testid="stTabs"] button { width:100% !important; justify-content:flex-start !important; }
          .stDataFrame, [data-testid="stDataFrame"] { overflow-x:auto !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_admin_password() -> str:
    env = os.getenv("ADMIN_ACCESS_PASSWORD", "").strip()
    if env:
        return env
    try:
        return str(st.secrets.get("admin", {}).get("password", "")).strip()
    except Exception:
        return ""


def setup_session() -> None:
    if "admin_until" not in st.session_state:
        st.session_state.admin_until = 0.0
    if time.time() >= float(st.session_state.get("admin_until", 0) or 0):
        st.session_state.is_admin = False
    st.session_state.setdefault("view", "painel")
    st.session_state.setdefault("team_count", 1)
    st.session_state.setdefault("team_form_context", "novo")


def admin_authenticated() -> bool:
    return bool(st.session_state.get("is_admin")) and time.time() < float(st.session_state.get("admin_until", 0) or 0)


def try_login(password: str) -> bool:
    expected = get_admin_password()
    if not expected:
        st.error("A senha administrativa ainda não está configurada. Preencha [admin].password em .streamlit/secrets.toml.")
        return False
    ok = hmac.compare_digest(password.encode("utf-8"), expected.encode("utf-8"))
    if ok:
        st.session_state.is_admin = True
        st.session_state.admin_until = time.time() + SESSION_HOURS * 3600
    return ok


def norm_text(value: Any) -> str:
    return " ".join(str(value or "").replace("°", "º").strip().split())



def fmt_num(value: Any) -> str:
    """Formata pontos como inteiro, usando ponto como separador de milhar."""
    try:
        if value is None or pd.isna(value):
            return "0"
        return f"{int(round(float(value))):,}".replace(",", ".")
    except (TypeError, ValueError, OverflowError):
        return "0"


def fmt_percentage(value: Any) -> str:
    """Percentual com uma casa decimal e convenção brasileira (vírgula)."""
    try:
        return f"{float(value):.1f}%".replace(".", ",")
    except (TypeError, ValueError, OverflowError):
        return "0,0%"


def uppercase_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Converte cabeçalhos e textos de tabelas apenas para apresentação."""
    result = frame.copy()
    result.columns = [str(column).upper() for column in result.columns]
    for column in result.columns:
        if pd.api.types.is_object_dtype(result[column].dtype) or pd.api.types.is_string_dtype(result[column].dtype):
            result[column] = result[column].map(lambda value: value.upper() if isinstance(value, str) else value)
    return result


def fmt_date(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)) or str(value).strip() == "":
        return "—"
    parsed = pd.to_datetime(value, errors="coerce", dayfirst=True)
    return parsed.strftime("%d/%m/%Y") if not pd.isna(parsed) else str(value)


def full_name(row: dict[str, Any]) -> str:
    function = norm_text(row.get("Função", "")).upper()
    name = norm_text(row.get("Nome de Guerra", "")).upper()
    if not name:
        return ""
    return f"{function} {name.upper()}".strip()


def active_roster(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    people = []
    for row in rows:
        name = norm_text(row.get("Nome de Guerra", ""))
        if name and is_active(row.get("Ativo", True)):
            people.append({**row, "Nome completo": full_name(row)})
    return sorted(people, key=lambda r: str(r.get("Nome completo", "")).casefold())


def point_catalog(type_rows: list[dict[str, Any]]) -> tuple[dict[str, float], list[str]]:
    points: dict[str, float] = {name: value for name, value in OCORRENCIAS_BASE}
    active_types: list[str] = []
    seen: set[str] = set()
    existing_names: set[str] = set()
    # Pontuação canônica original é preservada; tipos adicionais vêm da planilha.
    base_names = {n.casefold() for n, _ in OCORRENCIAS_BASE}
    for row in type_rows:
        name = norm_text(row.get("Tipo de OC", ""))
        if not name:
            continue
        existing_names.add(name.casefold())
        try:
            p = float(str(row.get("Pontos", 0)).replace(",", "."))
        except (ValueError, TypeError):
            p = 0.0
        if name.casefold() not in base_names:
            points[name] = p
        if is_active(row.get("Ativo", True)) and name.casefold() not in seen:
            active_types.append(name)
            seen.add(name.casefold())
    for name, _ in OCORRENCIAS_BASE:
        if name.casefold() not in existing_names and name.casefold() not in seen:
            active_types.append(name)
            seen.add(name.casefold())
    return points, sorted(active_types, key=str.casefold)


def pdf_report(
    frame: pd.DataFrame,
    title: str,
    subtitle: str,
    columns: list[str],
    summary: dict[str, str] | None = None,
) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from xml.sax.saxutils import escape

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=9 * mm, rightMargin=9 * mm, topMargin=9 * mm, bottomMargin=9 * mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitlePMRN", parent=styles["Title"], alignment=TA_CENTER, textColor=colors.HexColor("#41439a"), fontSize=15)
    small = ParagraphStyle("SmallPMRN", parent=styles["Normal"], fontSize=7, leading=9)
    elements = [
        Paragraph("Produtividade e Pontuação — 15º BPM PMRN", title_style),
        Paragraph(escape(title.upper()), styles["Heading2"]),
        Paragraph(escape(subtitle.upper()), small),
        Spacer(1, 3 * mm),
    ]
    if summary:
        summary_cells = [
            [
                Paragraph(escape(label.upper()), small)
                for label in summary
            ],
            [
                Paragraph(escape(str(value)), styles["BodyText"])
                for value in summary.values()
            ],
        ]
        summary_table = Table(
            summary_cells,
            colWidths=[doc.width / len(summary)] * len(summary),
        )
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0efe9")),
            ("BACKGROUND", (0, 1), (-1, 1), colors.white),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d5d0c4")),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d5d0c4")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.extend([
            Paragraph("INDICADORES DOS DADOS FILTRADOS", styles["Heading3"]),
            summary_table,
            Spacer(1, 4 * mm),
        ])
    else:
        elements.append(Spacer(1, 1 * mm))
    table_data = [[Paragraph(escape(col.upper()), small) for col in columns]]
    for _, row in frame.iterrows():
        vals = []
        for col in columns:
            value = row.get(col, "")
            if col == "Data":
                value = fmt_date(value)
            elif col == "Pontos":
                value = fmt_num(value)
            if isinstance(value, str):
                value = value.upper()
            vals.append(Paragraph(escape(str(value if value not in [None, ""] else "—")), small))
        table_data.append(vals)
    if len(table_data) == 1:
        table_data.append([Paragraph("Sem registros para os filtros selecionados", small)] + [Paragraph("", small) for _ in columns[1:]])
    widths = [doc.width / len(columns)] * len(columns)
    table = Table(table_data, repeatRows=1, colWidths=widths)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#41439a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d5d0c4")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f4ef")]),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(table)
    doc.build(elements)
    return buffer.getvalue()


def sidebar_filters(details: pd.DataFrame, facts: pd.DataFrame, people: list[dict[str, Any]], known_types: list[str]) -> dict[str, Any]:
    with st.sidebar:
        if st.session_state.pop("reset_filters_requested", False):
            for key in ["filter_start_date", "filter_end_date", "filter_company", "filter_division", "filter_people", "filter_types"]:
                st.session_state.pop(key, None)

        st.markdown("<h3 class='sidebar-title'>15º BPM PMRN</h3>", unsafe_allow_html=True)
        with st.container():
            _, logo_column, _ = st.columns([1, 2, 1])
            logo_column.image(
                str(LOGO_PATH),
                width=160,
                alt="Brasão do 15º BPM",
            )
        st.divider()
        st.markdown("#### FILTROS")
        available_dates = (
            details.get("Data", pd.Series(dtype=object)).tolist()
            + facts.get("Data", pd.Series(dtype=object)).tolist()
        )
        dates = [value for value in available_dates if isinstance(value, date)]
        valid_dates = sorted(set(dates))

        start_default = valid_dates[0] if valid_dates else date.today()
        end_default = valid_dates[-1] if valid_dates else date.today()

        start_date = st.date_input(
            "Data inicial",
            value=start_default,
            format="DD/MM/YYYY",
            key="filter_start_date",
        )

        end_date = st.date_input(
            "Data final",
            value=end_default,
            format="DD/MM/YYYY",
            key="filter_end_date",
        )
        if start_date > end_date:
            st.warning("A data inicial não pode ser posterior à data final.")

        # A estrutura do organograma é a fonte única de opções; não misturamos
        # subdivisões de outra Companhia apenas porque existem em dados históricos.
        company_options = ["Todos"] + list(COMPANHIAS)
        if st.session_state.get("filter_company") not in company_options:
            st.session_state["filter_company"] = "Todos"
        company = st.selectbox("Companhia", company_options, key="filter_company")
        allowed_divisions = list(COMPANHIAS[company]) if company != "Todos" else [d for group in COMPANHIAS.values() for d in group]
        division_options = ["Todos"] + allowed_divisions
        current_division = st.session_state.get("filter_division", "Todos")
        if current_division not in division_options:
            # Ao trocar a Companhia, zera uma Subdivisão que não pertence a ela.
            st.session_state["filter_division"] = "Todos"
        division = st.selectbox("Subdivisão", division_options, key="filter_division")

        active_names = [str(p.get("Nome completo", "")) for p in people if p.get("Nome completo")]
        all_names = sorted(set(active_names) | set(details.get("Efetivo", pd.Series(dtype=str)).dropna().astype(str)), key=str.casefold)
        selected_people = st.multiselect("Efetivo", all_names, placeholder="Todos", key="filter_people", help="Digite parte do nome neste campo para pesquisar e selecione um ou mais policiais.")
        fact_types = facts.get("Tipo de OC", pd.Series(dtype=str)).dropna().astype(str).tolist()
        types = sorted(set(known_types) | set(fact_types), key=str.casefold)
        selected_types = st.multiselect("Tipo de Ocorrência", types, placeholder="Todos", key="filter_types")
        st.divider()
        if st.button("Limpar filtros", use_container_width=True, key="clear_filters_bottom"):
            st.session_state.reset_filters_requested = True
            st.rerun()
    return {
        "start_date": start_date,
        "end_date": end_date,
        "company": company,
        "division": division,
        "people": selected_people,
        "types": selected_types,
    }


def apply_filters(details: pd.DataFrame, facts: pd.DataFrame, filters: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    d = details.copy()
    f = facts.copy()
    for frame in (d, f):
        if "Data" in frame.columns:
            frame.drop(
                frame.index[
                    ~frame["Data"].apply(
                        lambda value: isinstance(value, date)
                        and filters["start_date"] <= value <= filters["end_date"]
                    )
                ],
                inplace=True,
            )
            if filters["company"] != "Todos":
                frame.drop(frame.index[frame["Companhia"].astype(str) != filters["company"]], inplace=True)
            if filters["division"] != "Todos":
                frame.drop(frame.index[frame["Subdivisão"].astype(str) != filters["division"]], inplace=True)
    if filters["types"]:
        d = d[d["Tipo de OC"].isin(filters["types"])] if not d.empty else d
        f = f[f["Tipo de OC"].isin(filters["types"])] if not f.empty else f
    if filters["people"]:
        d = d[d["Efetivo"].isin(filters["people"])] if not d.empty else d
        matching_ids = set(d["ID"].astype(str)) if not d.empty else set()
        f = f[f["ID"].astype(str).isin(matching_ids)] if not f.empty else f
    return d.reset_index(drop=True), f.reset_index(drop=True)


def dashboard(details_all: pd.DataFrame, facts_all: pd.DataFrame, people: list[dict[str, Any]], known_types: list[str]) -> None:
    filters = sidebar_filters(details_all, facts_all, people, known_types)
    details, facts = apply_filters(details_all, facts_all, filters)
    filtered_summary = {
        "Ocorrências": str(int(facts["ID"].nunique()) if not facts.empty else 0),
        "Ocorrências por tipo": str(int(facts["Qtde"].sum()) if not facts.empty else 0),
        "Pontos das ocorrências": fmt_num(facts["Pontos"].sum()) if not facts.empty else "0",
        "% Pontos": fmt_percentage(percentage_of_total_points(facts, facts_all)),
    }
    st.markdown(f"<h1 class='main-title'>{APP_TITLE}</h1>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ocorrências", filtered_summary["Ocorrências"])
    c2.metric("Ocorrências por tipo", filtered_summary["Ocorrências por tipo"])
    c3.metric("Pontos das ocorrências", filtered_summary["Pontos das ocorrências"])
    c4.metric("% Pontos", filtered_summary["% Pontos"])

    with st.expander("Sobre o aplicativo e critérios de pontuação"):
        st.write("Os gráficos contam cada tipo de ocorrência uma vez por lançamento. O detalhamento e o ranking atribuem a pontuação individual a cada policial distinto presente nas equipes registradas.")
        st.dataframe(uppercase_frame(pd.DataFrame(OCORRENCIAS_BASE, columns=["Tipo de ocorrência", "Pontos base"])), use_container_width=True, hide_index=True)

    with st.container(border=True):
        st.subheader("Dados filtrados")
        if details.empty:
            st.info("Não há registros de efetivo para os filtros selecionados." if not details_all.empty else "Ainda não há lançamentos. Use ‘Adicionar dados’ para registrar a primeira ocorrência.")
        else:
            view = details.copy()
            view["Data"] = view["Data"].apply(fmt_date)
            view["Pontos"] = view["Pontos"].apply(fmt_num)
            st.dataframe(uppercase_frame(view[["Data", "Companhia", "Subdivisão", "Efetivo", "Tipo de OC", "Qtde", "Pontos"]]), use_container_width=True, hide_index=True, height=320)
            try:
                pdf = pdf_report(view, "Dados filtrados", f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", ["Data", "Companhia", "Subdivisão", "Efetivo", "Tipo de OC", "Qtde", "Pontos"], filtered_summary)
                st.download_button("Download em PDF — Resumo", pdf, file_name="15BPM_PMRN_resumo.pdf", mime="application/pdf")
            except Exception as exc:
                st.warning(f"Não foi possível gerar o PDF: {exc}")

    with st.container(border=True):
        st.subheader("Distribuição de Ocorrências por Companhia")
        dist_company = totals_by_dimension(facts, "Companhia")
        if not dist_company.empty:
            chart_data = dist_company.copy()
            chart_data["Companhia"] = chart_data["Companhia"].astype(str).str.upper()
            chart_data["_PctOcorrencias"] = chart_data["Porcentagem de Ocorrências"].map(fmt_percentage)
            chart_data["_PctPontos"] = chart_data["Porcentagem de Pontos"].map(fmt_percentage)
            chart = px.pie(chart_data, names="Companhia", values="Qtde", hole=0.48, custom_data=["_PctOcorrencias", "Pontos", "_PctPontos"])
            chart.update_traces(textposition="outside", texttemplate="%{label}<br>%{customdata[0]}", hovertemplate="%{label}<br>OCORRÊNCIAS: %{customdata[0]}<br>PONTOS: %{customdata[1]}<br>% PONTOS: %{customdata[2]}<extra></extra>")
            chart.update_layout(margin=dict(l=15, r=15, t=10, b=10), legend_title_text="COMPANHIA")
            st.plotly_chart(chart, use_container_width=True)
            display = dist_company.copy()
            display["Pontos"] = display["Pontos"].map(fmt_num)
            display["Porcentagem de Ocorrências"] = display["Porcentagem de Ocorrências"].map(fmt_percentage)
            display["Porcentagem de Pontos"] = display["Porcentagem de Pontos"].map(fmt_percentage)
            st.dataframe(uppercase_frame(display[["Companhia", "Qtde", "Pontos", "Porcentagem de Ocorrências", "Porcentagem de Pontos"]]), use_container_width=True, hide_index=True)
        else:
            st.info("Sem dados para a distribuição por Companhia.")
        st.divider()
        st.subheader("Distribuição de Ocorrências por Subdivisão")
        if not facts.empty:
            dist_division = facts.groupby(["Companhia", "Subdivisão"], dropna=False).agg(Qtde=("Qtde", "sum"), Pontos=("Pontos", "sum")).reset_index()
            total_q = float(dist_division["Qtde"].sum()) or 1.0
            total_p = float(dist_division["Pontos"].sum()) or 1.0
            dist_division["Porcentagem de Ocorrências"] = dist_division["Qtde"] / total_q * 100
            dist_division["Porcentagem de Pontos"] = dist_division["Pontos"] / total_p * 100
            chart2_data = dist_division.copy()
            chart2_data["Companhia"] = chart2_data["Companhia"].astype(str).str.upper()
            chart2_data["Subdivisão"] = chart2_data["Subdivisão"].astype(str).str.upper()
            chart2_data["_PctOcorrencias"] = chart2_data["Porcentagem de Ocorrências"].map(fmt_percentage)
            chart2_data["_PctPontos"] = chart2_data["Porcentagem de Pontos"].map(fmt_percentage)
            chart2 = px.pie(chart2_data, names="Subdivisão", values="Qtde", hole=0.48, custom_data=["Companhia", "_PctOcorrencias", "Pontos", "_PctPontos"])
            chart2.update_traces(textposition="outside", texttemplate="%{label}<br>%{customdata[1]}", hovertemplate="%{label}<br>COMPANHIA: %{customdata[0]}<br>OCORRÊNCIAS: %{customdata[1]}<br>PONTOS: %{customdata[2]}<br>% PONTOS: %{customdata[3]}<extra></extra>")
            chart2.update_layout(margin=dict(l=15, r=15, t=10, b=10), legend_title_text="SUBDIVISÃO")
            st.plotly_chart(chart2, use_container_width=True)
            display2 = dist_division.copy()
            display2["Pontos"] = display2["Pontos"].map(fmt_num)
            display2["Porcentagem de Ocorrências"] = display2["Porcentagem de Ocorrências"].map(fmt_percentage)
            display2["Porcentagem de Pontos"] = display2["Porcentagem de Pontos"].map(fmt_percentage)
            st.dataframe(uppercase_frame(display2[["Companhia", "Subdivisão", "Qtde", "Pontos", "Porcentagem de Ocorrências", "Porcentagem de Pontos"]]), use_container_width=True, hide_index=True)
        else:
            st.info("Sem dados para a distribuição por Subdivisão.")

    with st.container(border=True):
        st.subheader("Ranking de Produtividade")
        ranking = ranking_frame(details)
        if not ranking.empty:
            rank_view = ranking.copy()
            rank_view["Pontos"] = rank_view["Pontos"].map(fmt_num)
            rank_view.insert(0, "#", range(1, len(rank_view) + 1))
            st.dataframe(uppercase_frame(rank_view[["#", "Efetivo", "Companhia", "Subdivisão", "Qtde", "Pontos"]]), use_container_width=True, hide_index=True, height=300)
            pdf_frame = ranking.copy()
            pdf = pdf_report(pdf_frame, "Ranking de Produtividade", f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", ["Efetivo", "Companhia", "Subdivisão", "Qtde", "Pontos"], filtered_summary)
            st.download_button("Download em PDF — Ranking", pdf, file_name="15BPM_PMRN_ranking.pdf", mime="application/pdf")
            top = ranking.head(20).sort_values("Pontos", ascending=True)
            top_chart = top.copy()
            for col in ["Efetivo", "Companhia", "Subdivisão"]:
                top_chart[col] = top_chart[col].astype(str).str.upper()
            fig = px.bar(top_chart, x="Pontos", y="Efetivo", orientation="h", text="Pontos", hover_data=["Companhia", "Subdivisão", "Qtde"])
            fig.update_traces(marker_color="#41439a", textposition="outside")
            fig.update_layout(height=max(320, 36 * len(top)), margin=dict(l=10, r=50, t=10, b=10), yaxis_title=None, xaxis_title="PONTOS", showlegend=False)
            st.subheader("Efetivo x Pontos")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem pontos no ranking para os filtros selecionados.")
    st.markdown("<div class='app-footer'>Aplicativo desenvolvido para o 15º BPM — PMRN</div>", unsafe_allow_html=True)


def render_flash_message() -> None:
    message = st.session_state.pop("flash_message", None)
    kind = st.session_state.pop("flash_kind", "success")
    if not message:
        return
    if kind == "error":
        st.error(message)
    else:
        st.success(message)


def render_effective_admin(employee_ws, employee_rows: list[dict[str, Any]]) -> None:
    if st.session_state.pop("reset_employee_selection", False):
        st.session_state.pop("employee_edit_choice", None)
    st.subheader("Cadastro de efetivo")
    choices = ["Novo militar"] + [f"{r.get('Nome de Guerra','')} · {r.get('Função','')} · ID {r.get('ID','')}" for r in employee_rows]
    choice = st.selectbox("Selecione um cadastro para atualizar ou excluir", choices, key="employee_edit_choice")
    selected: dict[str, Any] = {}
    if choice != "Novo militar":
        selected = next((r for r in employee_rows if f"{r.get('Nome de Guerra','')} · {r.get('Função','')} · ID {r.get('ID','')}" == choice), {})
    funcs = FUNCOES[:]
    old_function = norm_text(selected.get("Função", "")).upper()
    if old_function and old_function not in funcs:
        funcs.append(old_function)
    form_context = str(selected.get("ID", "novo"))
    with st.form(f"employee_form_{form_context}", clear_on_submit=not bool(selected)):
        a, b = st.columns(2)
        function = a.selectbox("Função", funcs, index=funcs.index(old_function) if old_function in funcs else 0, key=f"emp_function_{form_context}")
        function = normalize_person_name(function)
        name_input = b.text_input(
            "Nome de Guerra",
            value=str(selected.get("Nome de Guerra", "")),
            key=f"emp_name_{form_context}",
            placeholder="EX.: JOÃO DA SILVA",
            help="Ao salvar, o nome fica em MAIÚSCULAS. Acentos, hífens e espaços entre palavras são preservados (Unicode UTF-8).",
        )
        name = normalize_person_name(name_input)
        active = st.checkbox("Militar ativo", value=is_active(selected.get("Ativo", True)), key=f"emp_active_{form_context}")
        submit_label = "Atualizar cadastro" if selected else "Cadastrar efetivo"
        submit = st.form_submit_button(submit_label, type="primary", use_container_width=True)
    if submit:
        if not name:
            st.error("Preencha o Nome de Guerra.")
            return
        duplicate = any(
            norm_text(r.get("Função", "")).casefold() == function.casefold()
            and norm_text(r.get("Nome de Guerra", "")).casefold() == name.casefold()
            and str(r.get("ID", "")) != str(selected.get("ID", ""))
            for r in employee_rows
        )
        if duplicate:
            st.error("Já existe um cadastro com a mesma Função e Nome de Guerra.")
            return
        payload = {"ID": str(selected.get("ID") or make_id()), "Função": function, "Nome de Guerra": name, "Ativo": bool(active), "Criado em": str(selected.get("Criado em") or record_timestamp())}
        try:
            if selected:
                row_n = int(selected.get("_row_number", 0))
                if row_n < 2:
                    raise ValueError("Não foi possível determinar a linha do cadastro selecionado.")
                update_mapping(employee_ws, row_n, {**selected, **payload})
            else:
                append_mapping(employee_ws, payload)
        except Exception:
            st.session_state.flash_message = "Erro ao atualizar efetivo no banco." if selected else "Erro ao cadastrar efetivo no banco."
            st.session_state.flash_kind = "error"
            st.rerun()
        st.session_state.flash_message = "Cadastro de efetivo atualizado com sucesso." if selected else "Efetivo cadastrado com sucesso."
        st.session_state.flash_kind = "success"
        st.cache_data.clear()
        st.session_state.pop("employee_delete_pending_id", None)
        st.rerun()

    if selected:
        st.markdown("#### Excluir cadastro")
        st.caption("A exclusão remove o cadastro da aba de efetivo. Os lançamentos históricos já registrados permanecem na planilha.")
        if st.button("Excluir efetivo selecionado", key=f"request_delete_employee_{form_context}", use_container_width=True):
            st.session_state.employee_delete_pending_id = str(selected.get("ID", ""))
            st.rerun()
        if str(st.session_state.get("employee_delete_pending_id", "")) == str(selected.get("ID", "")):
            st.warning(f"Confirma a exclusão do cadastro {full_name(selected)}? O histórico dos lançamentos não será apagado.")
            confirm_col, cancel_col = st.columns(2)
            if confirm_col.button("Confirmar exclusão", type="primary", key=f"confirm_delete_employee_{form_context}", use_container_width=True):
                try:
                    row_n = int(selected.get("_row_number", 0))
                    if row_n < 2:
                        raise ValueError("Linha de efetivo inválida para exclusão.")
                    employee_ws.delete_rows(row_n)
                except Exception:
                    st.session_state.flash_message = "Erro ao excluir efetivo do banco."
                    st.session_state.flash_kind = "error"
                    st.session_state.pop("employee_delete_pending_id", None)
                    st.rerun()
                st.session_state.flash_message = "Efetivo excluído com sucesso."
                st.session_state.flash_kind = "success"
                st.session_state.pop("employee_delete_pending_id", None)
                st.session_state.reset_employee_selection = True
                st.cache_data.clear()
                st.rerun()
            if cancel_col.button("Cancelar", key=f"cancel_delete_employee_{form_context}", use_container_width=True):
                st.session_state.pop("employee_delete_pending_id", None)
                st.rerun()

    if employee_rows:
        st.markdown("#### Efetivo cadastrado")
        df = pd.DataFrame([{"Função": r.get("Função", ""), "Nome de Guerra": r.get("Nome de Guerra", ""), "Nome completo": full_name(r), "Ativo": "Sim" if is_active(r.get("Ativo", True)) else "Não"} for r in employee_rows])
        st.dataframe(uppercase_frame(df.sort_values(["Função", "Nome de Guerra"], key=lambda col: col.astype(str).str.casefold())), use_container_width=True, hide_index=True)


def _active_type_names(type_rows: list[dict[str, Any]]) -> list[str]:
    return [str(r.get("Tipo de OC", "")).strip() for r in type_rows if str(r.get("Tipo de OC", "")).strip() and is_active(r.get("Ativo", True))]


def render_registered_launches(
    launch_ws,
    launch_rows: list[dict[str, Any]],
    launch_lookup: dict[str, dict[str, Any]],
    labels_by_id: dict[str, str],
    launch_members: Callable[[dict[str, Any]], list[str]],
    launch_types: Callable[[dict[str, Any]], list[str]],
    launch_sort_key: Callable[[dict[str, Any]], float],
) -> None:
    if not launch_rows:
        return

    st.markdown("#### Lançamentos registrados")
    available_dates = set()
    for row in launch_rows:
        parsed_date = pd.to_datetime(row.get("Data"), errors="coerce", dayfirst=True)
        if not pd.isna(parsed_date):
            available_dates.add(parsed_date.date())
    date_options = [value.strftime("%d/%m/%Y") for value in sorted(available_dates, reverse=True)]
    type_options = sorted(
        {kind for row in launch_rows for kind in launch_types(row)},
        key=str.casefold,
    )
    date_col, team_col, type_col = st.columns([1, 1.5, 1.5])
    if st.session_state.get("launch_list_date_filter", "Todas") not in ["Todas"] + date_options:
        st.session_state["launch_list_date_filter"] = "Todas"
    date_filter = date_col.selectbox(
        "Pesquisar por data",
        ["Todas"] + date_options,
        key="launch_list_date_filter",
    )
    team_filter = team_col.text_input(
        "Pesquisar por equipe",
        key="launch_list_team_filter",
        placeholder="Nome de policial",
    ).strip().casefold()
    if st.session_state.get("launch_list_type_filter", "Todos") not in ["Todos"] + type_options:
        st.session_state["launch_list_type_filter"] = "Todos"
    type_filter = type_col.selectbox(
        "Pesquisar por tipo de OC",
        ["Todos"] + type_options,
        key="launch_list_type_filter",
    )

    visible_launches = []
    for row in sorted(launch_rows, key=launch_sort_key, reverse=True):
        members = launch_members(row)
        kinds = launch_types(row)
        if date_filter != "Todas" and fmt_date(row.get("Data")) != date_filter:
            continue
        if team_filter and not any(team_filter in member.casefold() for member in members):
            continue
        if type_filter != "Todos" and type_filter not in kinds:
            continue
        visible_launches.append((row, members, kinds))

    pending_delete_id = str(st.session_state.get("pending_launch_delete", ""))
    pending_delete = launch_lookup.get(pending_delete_id)
    if pending_delete:
        pending_members = ", ".join(launch_members(pending_delete)) or "—"
        st.warning(
            f"Confirma a exclusão do lançamento de {fmt_date(pending_delete.get('Data'))} "
            f"da Companhia {pending_delete.get('Companhia', '—')} — equipe: {pending_members} — "
            f"tipo(s) de OC: {', '.join(launch_types(pending_delete)) or '—'}?"
        )
        confirm_col, cancel_col = st.columns(2)
        if confirm_col.button(
            "Confirmar exclusão",
            type="primary",
            use_container_width=True,
            key=f"confirm_delete_launch_{pending_delete_id}",
        ):
            row_number = int(pending_delete.get("_row_number", 0) or 0)
            if row_number < 2:
                st.error("Não foi possível excluir: o lançamento não possui uma linha válida na planilha.")
            else:
                try:
                    delete_launch(launch_ws, row_number)
                except Exception as exc:
                    st.error(f"Não foi possível excluir o lançamento: {exc}")
                else:
                    st.session_state.pop("pending_launch_delete", None)
                    st.session_state.flash_message = "Lançamento excluído com sucesso."
                    st.session_state.flash_kind = "success"
                    st.session_state.reset_launch_form = True
                    st.cache_data.clear()
                    st.rerun()
        if cancel_col.button(
            "Cancelar",
            use_container_width=True,
            key=f"cancel_delete_launch_{pending_delete_id}",
        ):
            st.session_state.pop("pending_launch_delete", None)
            st.rerun()
    elif pending_delete_id:
        st.session_state.pop("pending_launch_delete", None)

    if not visible_launches:
        st.info("Nenhum lançamento corresponde à pesquisa.")
        return

    with st.container(height=600, border=True):
        header_date, header_details, header_types, header_actions = st.columns(
            [1, 3, 1.3, 1.4]
        )
        header_date.caption("DATA")
        header_details.caption("COMPANHIA / EQUIPE")
        header_types.caption("TIPOS DE OC")
        header_actions.caption("AÇÕES")
        for row, members, kinds in visible_launches:
            row_id = str(row.get("ID", "")).strip()
            date_col, details_col, types_col, actions_col = st.columns([1, 3, 1.3, 1.4])
            date_col.write(fmt_date(row.get("Data")))
            details_col.write(str(row.get("Companhia", "")))
            details_col.caption(f"EQUIPE: {', '.join(members) or '—'}")
            types_col.write(", ".join(kinds) or "—")
            update_col, delete_col = actions_col.columns(2)
            if update_col.button(
                "Atualizar",
                key=f"update_launch_{row_id}",
                use_container_width=True,
            ):
                st.session_state["launch_action"] = "Editar lançamento existente"
                st.session_state["launch_edit_choice"] = labels_by_id[row_id]
                st.rerun()
            if delete_col.button(
                "Excluir",
                key=f"delete_launch_{row_id}",
                use_container_width=True,
            ):
                st.session_state["pending_launch_delete"] = row_id
                st.rerun()


def render_launch_admin(launch_ws, launch_rows: list[dict[str, Any]], employee_rows: list[dict[str, Any]], active_types: list[str], point_map: dict[str, float]) -> None:
    # Zera os widgets depois de salvar, preservando a autenticação administrativa.
    if st.session_state.get("reset_launch_form"):
        for state_key in list(st.session_state.keys()):
            if str(state_key).startswith(("role_", "launch_types_", "launch_date_", "launch_quantity_", "launch_ammo_", "launch_company_", "launch_division_")):
                st.session_state.pop(state_key, None)
        st.session_state.team_count = 1
        st.session_state.pop("launch_action", None)
        st.session_state.pop("launch_edit_choice", None)
        st.session_state.reset_launch_form = False
    removed_team_idx = st.session_state.pop("clear_removed_team_index", None)
    if removed_team_idx is not None:
        for role in ROLES:
            st.session_state.pop(f"role_{removed_team_idx}_{role}", None)

    st.subheader("Adicionar dados — lançamento operacional")

    def launch_members(row: dict[str, Any]) -> list[str]:
        return [
            str(value).strip()
            for key, value in row.items()
            if re.fullmatch(r"Equipe\s+\d+\s+-\s+(Cmt|Mot|P1|P2)", str(key), re.I)
            and str(value or "").strip()
        ]

    def launch_types(row: dict[str, Any]) -> list[str]:
        numbered = []
        for key, value in row.items():
            match = re.fullmatch(r"Tipo OC\s*(\d+)", str(key), re.I)
            if match and str(value or "").strip():
                numbered.append((int(match.group(1)), str(value).strip()))
        return [value for _, value in sorted(numbered)]

    def launch_sort_key(row: dict[str, Any]) -> float:
        parsed = pd.to_datetime(row.get("Data"), errors="coerce", dayfirst=True)
        return parsed.timestamp() if not pd.isna(parsed) else 0.0

    launch_lookup = {
        str(row.get("ID", "")): row
        for row in launch_rows
        if str(row.get("ID", "")).strip()
    }
    labels_by_id: dict[str, str] = {}
    for row in sorted(launch_rows, key=launch_sort_key, reverse=True):
        row_id = str(row.get("ID", "")).strip()
        members = ", ".join(launch_members(row))
        labels_by_id[row_id] = (
            f"{fmt_date(row.get('Data'))} · {row.get('Companhia', '')} · "
            f"{members[:65]} · ID {row_id}"
        )

    modes = ["Novo lançamento", "Editar lançamento existente"] if launch_rows else ["Novo lançamento"]
    mode = st.radio("Ação", modes, horizontal=True, key="launch_action")
    existing: dict[str, Any] | None = None
    if mode == "Editar lançamento existente":
        labels = list(labels_by_id.values())
        lookup = {labels_by_id[row_id]: row for row_id, row in launch_lookup.items()}
        if st.session_state.get("launch_edit_choice") not in labels:
            st.session_state.pop("launch_edit_choice", None)
        choice = st.selectbox("Selecione o lançamento", labels, key="launch_edit_choice")
        existing = lookup.get(choice)

    context = "novo" if existing is None else str(existing.get("ID", ""))
    if st.session_state.get("team_form_context") != context:
        st.session_state.team_form_context = context
        team_numbers = []
        for key, value in (existing or {}).items():
            match_team = re.fullmatch(r"Equipe\s+(\d+)\s+-\s+(Cmt|Mot|P1|P2)", str(key), re.I)
            if match_team and str(value or "").strip():
                team_numbers.append(int(match_team.group(1)))
        st.session_state.team_count = max(1, max(team_numbers or [1]))
        for state_key in list(st.session_state.keys()):
            if str(state_key).startswith("role_"):
                st.session_state.pop(state_key, None)

    roster = active_roster(employee_rows)
    all_names = [str(p["Nome completo"]) for p in roster]

    def role_options(key: str) -> list[str]:
        current = str(st.session_state.get(key, ""))
        opts = ["— Não selecionado —"] + all_names
        if current and current not in opts:
            opts.append(current)
        return opts

    existing_types: list[str] = []
    existing_num = 1
    existing_ammo = 1
    if existing:
        numbered_types = []
        for key, value in existing.items():
            match_type = re.fullmatch(r"Tipo OC\s*(\d+)", str(key), re.I)
            if match_type and str(value or "").strip():
                numbered_types.append((int(match_type.group(1)), str(value).strip()))
        existing_types = [value for _, value in sorted(numbered_types)]
        try:
            existing_num = int(float(str(existing.get("Quantidade informada", 1)).replace(",", ".")))
        except Exception:
            existing_num = 1
        try:
            existing_ammo = int(float(str(existing.get("Quantidade de munições", 1)).replace(",", ".")))
        except Exception:
            existing_ammo = 1

    with st.container(border=True):
        st.markdown("#### Dados do lançamento")
        c1, c2, c3 = st.columns(3)
        current_date = date.today()
        parsed_date = pd.to_datetime(existing.get("Data"), errors="coerce", dayfirst=True) if existing else pd.NaT
        if not pd.isna(parsed_date):
            current_date = parsed_date.date()
        date_key = f"launch_date_{context}"
        if date_key not in st.session_state:
            st.session_state[date_key] = current_date
        record_date = c1.date_input("Data", format="DD/MM/YYYY", key=date_key)

        company_options = ["— Selecione a Companhia —"] + list(COMPANHIAS)
        company_key = f"launch_company_{context}"
        old_company = normalize_org_label(existing.get("Companhia", "")) if existing else ""
        if company_key not in st.session_state:
            st.session_state[company_key] = next((co for co in COMPANHIAS if normalize_org_label(co) == old_company), "— Selecione a Companhia —")
        if st.session_state.get(company_key) not in company_options:
            st.session_state[company_key] = "— Selecione a Companhia —"
        company = c2.selectbox("Companhia", company_options, key=company_key)

        subdivisions = list(COMPANHIAS.get(company, []))
        division_options = ["— Selecione a Subdivisão —"] + subdivisions
        division_key = f"launch_division_{context}"
        old_division = normalize_org_label(existing.get("Subdivisão", "")) if existing else ""
        if division_key not in st.session_state:
            st.session_state[division_key] = next((d for d in subdivisions if normalize_org_label(d) == old_division), "— Selecione a Subdivisão —")
        if st.session_state.get(division_key) not in division_options:
            # A Companhia mudou: não conserva uma Subdivisão pertencente a outra.
            st.session_state[division_key] = "— Selecione a Subdivisão —"
        division = c3.selectbox("Subdivisão", division_options, key=division_key, disabled=company not in COMPANHIAS)
        if company in COMPANHIAS:
            st.caption(f"Subdivisões disponíveis para {company}: {len(subdivisions)}")

    st.markdown("#### Composição das equipes")
    add_col, remove_col, note_col = st.columns([1.2, 1.2, 2.6])
    if add_col.button("＋ Adicionar equipe", type="secondary", use_container_width=True, disabled=int(st.session_state.team_count) >= 10, key=f"add_team_{context}"):
        st.session_state.team_count = min(10, int(st.session_state.team_count) + 1)
        st.rerun()
    if remove_col.button("− Remover última", use_container_width=True, disabled=int(st.session_state.team_count) <= 1, key=f"remove_team_{context}"):
        removed_idx = int(st.session_state.team_count)
        st.session_state.team_count = max(1, removed_idx - 1)
        st.session_state.clear_removed_team_index = removed_idx
        st.rerun()
    note_col.caption(f"{int(st.session_state.team_count)} equipe(s) configurada(s). Cada equipe comporta Cmt, Mot, P1 e P2.")

    # Os seletores são widgets reativos fora de um st.form; assim a subdivisão
    # acompanha imediatamente a Companhia e os valores ficam preservados ao adicionar equipes.
    for team_idx in range(1, int(st.session_state.team_count) + 1):
        with st.container(border=True):
            st.markdown(f"**Equipe {team_idx}**")
            role_cols = st.columns(4)
            for role, col in zip(ROLES, role_cols):
                key = f"role_{team_idx}_{role}"
                old_value = str(existing.get(f"Equipe {team_idx} - {role}", "")) if existing else ""
                if key not in st.session_state:
                    st.session_state[key] = old_value if old_value else "— Não selecionado —"
                options = role_options(key)
                current_value = str(st.session_state.get(key, old_value or "— Não selecionado —"))
                if current_value not in options:
                    options.append(current_value)
                index = options.index(current_value) if current_value in options else 0
                col.selectbox(role, options, index=index, key=key, help="Digite parte do nome para pesquisar na lista.")

    st.markdown("#### Tipo de OC")
    type_options_for_form = list(active_types)
    for old_type_name in existing_types:
        if old_type_name not in type_options_for_form:
            type_options_for_form.append(old_type_name)
    default_types = [t for t in existing_types if t in type_options_for_form]
    types_key = f"launch_types_{context}"
    if types_key not in st.session_state:
        st.session_state[types_key] = default_types
    selected_types = st.multiselect("Selecione um ou mais tipos de ocorrência", type_options_for_form, key=types_key, placeholder="Pesquisar e selecionar tipos")

    colq1, colq2 = st.columns(2)
    selected_has_common = any(not t.startswith("MUNIÇÃO") and not t.startswith("ENTORPECENTE") for t in selected_types)
    selected_has_ammo = any(t.startswith("MUNIÇÃO") for t in selected_types)
    selected_has_drugs = any(t.startswith("ENTORPECENTE") for t in selected_types)
    quantity_key, ammo_key = f"launch_quantity_{context}", f"launch_ammo_{context}"
    if quantity_key not in st.session_state:
        st.session_state[quantity_key] = max(1, existing_num)
    if ammo_key not in st.session_state:
        st.session_state[ammo_key] = max(1, existing_ammo)
    quantity = colq1.number_input("Quantidade do item (para tipos comuns)", min_value=1, max_value=100000, step=1, disabled=not selected_has_common, key=quantity_key)
    ammo_quantity = colq2.number_input("Quantidade de munições apreendidas", min_value=1, max_value=100000, step=1, disabled=not selected_has_ammo, key=ammo_key)
    if selected_has_drugs:
        st.caption("Para as categorias de entorpecentes, a pontuação segue a faixa/peso cadastrada; Qtde individual permanece 1 por tipo selecionado.")
    if selected_types:
        preview = []
        seen_preview: set[str] = set()
        from scoring import ammo_tier, calculate_points, is_entorpecente, is_municao
        for typ in selected_types:
            eff = ammo_tier(int(ammo_quantity)) if is_municao(typ) else typ
            if eff.casefold() in seen_preview:
                continue
            seen_preview.add(eff.casefold())
            q = 1 if is_entorpecente(eff) or is_municao(eff) else int(quantity)
            p = float(point_map.get(eff, PTS_BASE.get(eff, 0))) if is_entorpecente(eff) or is_municao(eff) else float(calculate_points(eff, q, point_map))
            preview.append({"Tipo de OC gravado": eff, "Qtde por policial": q, "Pontos por policial": fmt_num(p), "Pontos da ocorrência (contados uma vez)": fmt_num(p)})
        st.dataframe(uppercase_frame(pd.DataFrame(preview)), use_container_width=True, hide_index=True)
        st.caption("A ocorrência é contabilizada uma vez nos gráficos de Companhia/Subdivisão; a pontuação é atribuída individualmente a cada policial distinto da equipe.")

    submit_label = "Salvar alterações" if existing else "Adicionar dados"
    submit = st.button(submit_label, type="primary", use_container_width=True, key=f"save_launch_{context}")
    render_registered_launches(
        launch_ws,
        launch_rows,
        launch_lookup,
        labels_by_id,
        launch_members,
        launch_types,
        launch_sort_key,
    )
    if not submit:
        return

    if company not in COMPANHIAS:
        st.error("Selecione uma Companhia do organograma.")
        return
    if division not in COMPANHIAS[company]:
        st.error("Selecione uma Subdivisão pertencente à Companhia escolhida.")
        return

    selected_members: list[str] = []
    teams: list[dict[str, str]] = []
    for team_idx in range(1, int(st.session_state.team_count) + 1):
        team: dict[str, str] = {}
        for role in ROLES:
            val = str(st.session_state.get(f"role_{team_idx}_{role}", "")).strip()
            team[role] = "" if not val or val == "— Não selecionado —" else val
            if team[role]:
                selected_members.append(team[role])
        teams.append(team)
    selected_members = list(dict.fromkeys(selected_members))
    if not selected_members:
        st.error("Selecione pelo menos um policial em uma das equipes.")
        return
    if not selected_types:
        st.error("Selecione pelo menos um Tipo de OC.")
        return

    payload: dict[str, Any] = {
        "ID": str(existing.get("ID")) if existing else make_id(),
        "Data": record_date.isoformat(),
        "Companhia": company,
        "Subdivisão": division,
        "Quantidade informada": int(quantity),
        "Quantidade de munições": int(ammo_quantity),
        # No lançamento novo, `existing` é None. Trate esse caso antes de chamar .get().
        "Criado em": str((existing or {}).get("Criado em") or record_timestamp()),
    }
    for idx, team in enumerate(teams, start=1):
        for role in ROLES:
            payload[f"Equipe {idx} - {role}"] = team[role]

    resolved_types: list[str] = []
    from scoring import ammo_tier, is_municao
    ammo_minimums = {
        "MUNIÇÃO 1 - 10": 1,
        "MUNIÇÃO 11 - 20": 11,
        "MUNIÇÃO 21 - 50": 21,
        "MUNIÇÃO 51 - 100": 51,
        "MUNIÇÃO 101 ou mais": 101,
    }
    selected_ammo = [str(t).strip() for t in selected_types if is_municao(str(t))]
    if selected_ammo:
        selected_floor = max(ammo_minimums.get(t.upper(), 1) for t in selected_ammo)
        if int(ammo_quantity) < selected_floor:
            ammo_quantity = selected_floor
            payload["Quantidade de munições"] = int(ammo_quantity)
    for typ in selected_types:
        effective_type = ammo_tier(int(ammo_quantity)) if is_municao(typ) else typ
        if effective_type.casefold() not in {x.casefold() for x in resolved_types}:
            resolved_types.append(effective_type)
    for idx, typ in enumerate(resolved_types, start=1):
        payload[f"Tipo OC {idx}"] = typ
    row_n = int(existing.get("_row_number", 0)) if existing else None
    try:
        save_launch(launch_ws, payload, row_n or None)
    except Exception:
        st.session_state.flash_message = "Erro ao atualizar dados no banco." if existing else "Erro ao adicionar dados ao banco."
        st.session_state.flash_kind = "error"
        st.rerun()
    st.session_state.flash_message = "Dados atualizados no banco com sucesso." if existing else "Dados adicionados ao banco com sucesso."
    st.session_state.flash_kind = "success"
    st.cache_data.clear()
    st.session_state.reset_launch_form = True
    st.session_state.view = "painel"
    st.rerun()


def render_admin(book, tabs: dict[str, Any]) -> None:
    if not admin_authenticated():
        st.markdown(f"<h1 class='main-title'>{APP_TITLE}</h1>", unsafe_allow_html=True)
        st.subheader("Adicionar dados / Administração")
        st.info("O painel é de consulta. A inclusão e edição de lançamentos e do efetivo exigem senha administrativa.")
        with st.form("admin_login"):
            password = st.text_input("Senha administrativa", type="password")
            submit = st.form_submit_button("Entrar", type="primary", use_container_width=True)
        if submit:
            if try_login(password):
                st.success("Acesso autorizado.")
                st.rerun()
            else:
                st.error("Senha incorreta ou ainda não configurada.")
        if not get_admin_password():
            st.warning("Configure [admin].password em .streamlit/secrets.toml antes de utilizar os formulários.")
        return

    st.markdown(f"<h1 class='main-title'>Administração — {PAGE_TITLE}</h1>", unsafe_allow_html=True)
    nav_back, nav_exit = st.columns(2)
    if nav_back.button("← Voltar ao painel", type="primary", use_container_width=True, key="admin_back_to_dashboard"):
        st.session_state.view = "painel"
        st.rerun()
    if nav_exit.button("Sair da administração", use_container_width=True, key="admin_sign_out"):
        st.session_state.is_admin = False
        st.session_state.admin_until = 0
        st.session_state.view = "painel"
        st.rerun()

    # Reload once per rerun to reflect data saved in previous operations.
    employee_rows, launch_rows, type_rows = load_sheet_rows(spreadsheet_id())
    point_map, active_types = point_catalog(type_rows)
    tab1, tab2, tab3 = st.tabs(["Adicionar dados / Editar lançamento", "Cadastrar efetivo", "Tipos de OC"])
    with tab1:
        render_launch_admin(tabs["launches"], launch_rows, employee_rows, active_types, point_map)
    with tab2:
        render_effective_admin(tabs["employees"], employee_rows)
    with tab3:
        st.subheader("Catálogo de tipos de ocorrência")
        st.caption("As categorias originais e seus pesos permanecem preservados. Para acrescentar categoria específica do 15º BPM, ela deve ser adicionada à aba ‘Tipos OC’ na planilha, com ID, Tipo de OC, Pontos, Ativo e Criado em.")
        types_df = pd.DataFrame([{"Tipo de OC": r.get("Tipo de OC", ""), "Pontos": r.get("Pontos", ""), "Ativo": "Sim" if is_active(r.get("Ativo", True)) else "Não"} for r in type_rows])
        if not types_df.empty:
            st.dataframe(uppercase_frame(types_df.sort_values("Tipo de OC", key=lambda s: s.astype(str).str.casefold())), use_container_width=True, hide_index=True, height=450)
        st.info("Por segurança, esta tela é de consulta. Não há função de exclusão de tipos nem de lançamentos nesta versão.")


@st.cache_resource(show_spinner=False)
def get_book_and_tabs():
    book = create_spreadsheet_client()
    tabs = initialize_schema(book, OCORRENCIAS_BASE)
    return book, tabs


@st.cache_data(ttl=10, show_spinner=False)
def load_sheet_rows(sheet_id: str):
    # sheet_id integra a chave de cache; as mutações limpam este cache logo após salvar.
    _, tabs = get_book_and_tabs()
    return read_rows(tabs["employees"]), read_rows(tabs["launches"]), read_rows(tabs["types"])


def main() -> None:
    inject_css()
    setup_session()
    # Atualização automática do painel: consulta novos lançamentos em intervalos curtos,
    # sem botão manual. As escritas limpam o cache e forçam a atualização imediata.
    if st.session_state.view == "painel":
        st_autorefresh(interval=15_000, limit=None, key="15bpm-live-refresh")
    with st.spinner("Carregando Aplicativo"):
        try:
            book, tabs = get_book_and_tabs()
            employee_rows, launch_rows, type_rows = load_sheet_rows(spreadsheet_id())
            point_map, active_types = point_catalog(type_rows)
            details_all, facts_all, _ = build_frames(launch_rows, point_map)
        except SheetsSetupError as exc:
            st.markdown(f"<h1 class='main-title'>{APP_TITLE}</h1>", unsafe_allow_html=True)
            st.error(str(exc))
            st.markdown("### Como corrigir")
            st.markdown("1. Configure as credenciais da conta de serviço em `Settings > Secrets` no Streamlit Cloud, conforme o `README.md`.\n2. Localmente, salve o JSON em `.streamlit/google-service-account.json`.\n3. Compartilhe a planilha com o e-mail `client_email` da conta de serviço como **Editor**.\n4. Confira `google_sheets.spreadsheet_id`, configure a senha administrativa e reinicie o aplicativo.")
            st.stop()
        except Exception as exc:
            st.error(f"Falha inesperada ao abrir a planilha: {exc}")
            st.stop()

    if st.session_state.view == "painel":
        toolbar_left, toolbar_button = st.columns([4, 1.6])
        with toolbar_button:
            if st.button("＋ Adicionar dados", type="primary", use_container_width=True, key="open_add_data"):
                st.session_state.view = "admin"
                st.rerun()
    render_flash_message()
    if st.session_state.view == "admin":
        render_admin(book, tabs)
    else:
        dashboard(details_all, facts_all, active_roster(employee_rows), active_types)


if __name__ == "__main__":
    main()

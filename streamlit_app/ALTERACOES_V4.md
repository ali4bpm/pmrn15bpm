# 15BPM_PMRN — Correção v4

- Corrige o erro `AttributeError: 'NoneType' object has no attribute 'get'` ao criar um novo lançamento.
- Reforça a centralização do brasão na barra lateral.
- Nome de Guerra é salvo em maiúsculas com preservação de acentos, hífens e espaços internos, usando normalização Unicode NFC.
- Não altera a autenticação Google, o ID da planilha, a composição de equipes nem os cálculos de pontuação.

Para atualizar uma instalação existente, copie `app.py`, `organization.py` e `text_utils.py` da atualização incremental para a pasta principal do projeto. Preserve os arquivos reais de `.streamlit`.

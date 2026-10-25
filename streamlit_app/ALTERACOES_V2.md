# 15BPM_PMRN — Ajustes da interface (versão 2)

## O que mudou
- Removido o botão manual “Atualizar dados”; painel consulta mudanças automaticamente a cada 15 segundos e atualiza imediatamente após gravações feitas pelo app.
- Removido o link que abria a planilha do Google Sheets no painel.
- O botão “Limpar filtros” agora ocupa essa área no fim dos filtros.
- Logo e título da sidebar centralizados.
- Botão “Adicionar dados” ampliado para ficar legível.
- Removido o texto auxiliar solicitado no painel e no formulário de lançamento.
- Removido o campo separado “Pesquisar”; a pesquisa por nome fica no próprio multiselect de Efetivo.
- Mantidos os filtros múltiplos de Efetivo e Tipo de Ocorrência; o catálogo de tipos está disponível mesmo antes do primeiro lançamento.
- Data do formulário exibida em DD/MM/AAAA.
- Companhia/Subdivisão limitadas aos itens definidos pelo organograma.
- Cadastro de efetivo com opções explícitas para atualizar e excluir, com confirmação antes de apagar. A exclusão do cadastro não apaga os lançamentos históricos.
- Mensagens de gravação são exibidas após o recarregamento: sucesso ou erro de inclusão/edição.
- Removidas as caixas vazias causadas por marcadores HTML abertos/fechados em blocos Markdown separados.

## Atualização sem perder credenciais
O arquivo incremental contém apenas `app.py`, `requirements.txt` e `README.md`. Copie-os para a pasta do projeto atual e substitua os arquivos quando solicitado. **Não substitua nem apague** `.streamlit/secrets.toml` e `.streamlit/google-service-account.json`.

Depois execute `1_INSTALAR_DEPENDENCIAS.bat` para instalar `streamlit-autorefresh`, então execute `3_TESTAR_GOOGLE_SHEETS.bat` e `2_INICIAR_APP.bat`.

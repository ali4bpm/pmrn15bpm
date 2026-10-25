# 15BPM_PMRN — Atualização de interface e equipes (versão 3)

## Alterações
- Companhia e Subdivisão agora seguem uma única tabela de hierarquia baseada no organograma enviado.
- O filtro de Subdivisão é reiniciado para “Todos” quando não pertence à Companhia escolhida.
- No lançamento, a seleção de Companhia atualiza imediatamente a lista de Subdivisões; opções incompatíveis são removidas e a gravação exige uma combinação válida.
- O formulário de lançamento usa controles reativos fora de `st.form`, para que os seletores e o botão + de equipe respondam na hora sem apagar valores já preenchidos.
- Botões “＋ Adicionar equipe” e “− Remover última” ficam acima da composição, com suporte para até dez equipes; cada equipe contém Cmt, Mot, P1 e P2.
- Navegação administrativa com botões maiores “Voltar ao painel” e “Sair da administração”.
- Layout CSS responsivo: colunas quebram em duas colunas em telas médias e em uma coluna em telefones; a sidebar pode recolher-se automaticamente.
- Nome de Guerra é normalizado para maiúsculas, preservando letras acentuadas, hífens e espaços internos (espaços repetidos são reduzidos a um).
- O seletor de efetivo em cada função da equipe permite digitar para pesquisar.

## Aplicar sem perder credenciais
Copie `app.py`, `organization.py` e `text_utils.py` desta atualização para a pasta principal existente e substitua `app.py` quando solicitado. Copie os arquivos de teste incluídos para a pasta `tests` (criando-a se necessário). **Não substitua** `.streamlit/secrets.toml` ou `.streamlit/google-service-account.json`.

Depois, inicie com `2_INICIAR_APP.bat`. Não é necessária nova instalação de dependências para esta atualização. Se quiser executar os testes locais, use `python -m pytest tests` no ambiente virtual do projeto.

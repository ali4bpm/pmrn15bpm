# 15BPM_PMRN — versão com Google Sheets (v4 corrigida)

Aplicação de consulta, produtividade e pontuação do 15º BPM/PMRN. Esta versão deixa de usar o Supabase e utiliza a planilha Google indicada pelo projeto como armazenamento de dados.

**Título da página:** `15BPM_PMRN`
**Planilha vinculada:** [Abrir Google Sheets](https://docs.google.com/spreadsheets/d/1fuZYlIANUvqA0PpIhVENef_b9DMIGFhd4R_9M2Atjao/edit)

## O que foi alterado

- O navegador mostra o título `15BPM_PMRN` e o brasão do 15º BPM como ícone/favicon e imagem de identificação no painel.
- A aba `Efetivo 15BPM` fica no início e guarda `Função`, `Nome de Guerra`, estado ativo e identificadores.
- A aba `Lançamentos` armazena **uma linha por inclusão**. Os nomes de cada equipe ficam em colunas de função (`Equipe 1 - Cmt`, `Equipe 1 - Mot`, `Equipe 1 - P1`, `Equipe 1 - P2` etc.); uma mesma linha pode conter várias equipes e vários tipos de OC. O aplicativo reserva colunas para até 10 equipes (Cmt/Mot/P1/P2) e vários tipos; se necessário, novas colunas de tipos são criadas automaticamente.
- A aba `Tipos OC` traz as categorias e pontuações-base da aplicação original. Na primeira inicialização, os tipos ausentes são acrescentados sem excluir abas ou linhas existentes.
- O painel oferece filtros por período, Companhia, Subdivisão, efetivo e tipo de ocorrência, dados detalhados, ranking, gráficos de distribuição e exportação em PDF.
- Os PDFs de resumo e ranking incluem o título institucional e os indicadores filtrados de ocorrências, ocorrências por tipo, pontos e percentual de pontos.
- O indicador `% Pontos` mostra a participação dos pontos filtrados no total geral. O ranking acumula ocorrências e pontos por policial, mesmo quando ele aparece em mais de uma Companhia ou Subdivisão.
- A inclusão e a edição exigem senha administrativa. A lista de lançamentos permite pesquisar por data, equipe e tipo de OC, além de atualizar ou excluir cada lançamento com confirmação. O cadastro de efetivo também oferece atualização e exclusão; remover um policial não apaga lançamentos históricos.
- O painel atualiza automaticamente em intervalos de 15 segundos, sem botão manual de atualização. Depois de uma gravação feita no próprio aplicativo, o painel é atualizado imediatamente.

## Organograma e responsividade (versão 3)

As opções de Companhia e Subdivisão obedecem estritamente ao organograma:

- **1ª CPM/Sede Santa Cruz:** 1º Pelotão — Santa Cruz; DPM de Campo Redondo; DPM de Lajes Pintadas.
- **2ª CPM/Sede Tangará:** 1º Pelotão — Tangará; DPM de Sítio Novo; DPM de Serra Caiada; DPM de Boa Saúde; DPM de Sen. Elói de Souza.
- **3ª CPM/Sede Santa Cruz:** 1º Pelotão — Jaçanã; DPM de Cel. Ezequiel; DPM de Japi; DPM de São Bento do Trairi.

Ao trocar a Companhia, o seletor de Subdivisão é atualizado imediatamente e limpa um valor que não pertença à nova Companhia. Em telefones e tablets, os campos são reagrupados em colunas mais largas para facilitar a seleção. O formulário usa botões separados para adicionar/remover equipes e o botão principal para salvar o lançamento.
Nomes de guerra são salvos em maiúsculas, preservando acentos, hífens e espaços internos entre nomes; espaços repetidos são normalizados.

## Regra para equipes e contagem de ocorrência

O registro original da planilha é sempre um lançamento único com um ID.

- **Gráficos de Companhia/Subdivisão:** cada tipo de OC selecionado conta uma vez por lançamento, independentemente de quantos policiais e equipes estejam associados. A pontuação da ocorrência também entra uma vez nesses totais.
- **Dados filtrados e ranking:** o lançamento é expandido para cada policial distinto associado às posições Cmt, Mot, P1 e P2 de todas as equipes. Cada policial recebe os pontos individuais de cada tipo selecionado, seguindo as regras de pontuação originais.
- Se a mesma pessoa for preenchida duas vezes na composição do mesmo lançamento, ela é contabilizada apenas uma vez naquele lançamento para evitar duplicidade. A pessoa ainda pode aparecer em lançamentos diferentes normalmente.
- A aplicação conserva os campos de quantidade e a regra de faixa de munições da versão anterior: munições e categorias de entorpecentes contabilizam Qtde individual 1 por tipo registrado; os demais tipos usam a quantidade informada e o cálculo original de pontos.

## Requisitos

- Windows 10/11;
- Python 3.11 ou 3.12 (preferencial), disponível pelo comando `py`;
- conexão à internet durante a instalação e para usar o Google Sheets;
- permissão para editar a planilha e para habilitar as APIs no Google Cloud.

## Parte 1 — habilitar acesso à planilha

A API não consegue gravar dados apenas com o endereço de compartilhamento da planilha. A maneira utilizada aqui é uma **conta de serviço do Google**, que recebe acesso somente às planilhas que forem compartilhadas diretamente com ela. A documentação da biblioteca `gspread` explica esse modelo e a necessidade de compartilhar a planilha com o e-mail da conta de serviço: [autenticação gspread](https://docs.gspread.org/en/master/oauth2.html).

1. Abra [Google Cloud Console](https://console.cloud.google.com/) com a conta autorizada a configurar o projeto (pode ser `pmrn10cipm@gmail.com`). Crie um projeto, por exemplo, `15BPM_PMRN_Sheets`.
2. Em **APIs e serviços → Biblioteca**, habilite **Google Sheets API** e **Google Drive API**. O guia oficial do Google descreve a habilitação de API e a configuração inicial: [Google Sheets API — quickstart](https://developers.google.com/workspace/sheets/api/quickstart/python).
3. Em **IAM e administrador → Contas de serviço**, crie uma conta de serviço, por exemplo `15bpm-sheets-app`. Não é necessário conceder a ela um papel amplo no projeto para esta planilha; o acesso aos dados será concedido na própria planilha.
4. Abra a conta de serviço criada, acesse **Chaves → Adicionar chave → Criar nova chave → JSON**. O Google baixará um arquivo `.json`. Faça isso apenas em uma máquina confiável. O Google explica esse procedimento e alerta para guardar com segurança a chave privada: [criar chaves de conta de serviço](https://cloud.google.com/iam/docs/keys-create-delete).
5. No Explorador de Arquivos, abra a pasta deste projeto e coloque o JSON baixado em:

   `.streamlit\google-service-account.json`

   Renomeie o arquivo para esse nome exato. **Não cole o conteúdo do JSON em conversas, e-mail ou GitHub.** Ele contém uma chave privada.
6. Abra o JSON localmente no Bloco de Notas e copie apenas o valor de `client_email` (o endereço termina em `iam.gserviceaccount.com`).
7. Abra a planilha [15BPM_PMRN](https://docs.google.com/spreadsheets/d/1fuZYlIANUvqA0PpIhVENef_b9DMIGFhd4R_9M2Atjao/edit), clique em **Compartilhar** e adicione aquele endereço de conta de serviço como **Editor**. Não compartilhe a senha da conta Google nem altere o compartilhamento para “qualquer pessoa com o link”.
8. Aguarde um pouco e teste o acesso executando `3_TESTAR_GOOGLE_SHEETS.bat`. O teste mostra apenas o e-mail técnico e o estado da conexão; ele não exibe a chave privada.

> Se a organização PMRN bloquear a criação de contas de serviço/chaves, não tente contornar a política institucional. Solicite ao administrador Google Workspace uma alternativa de autenticação aprovada.

## Parte 2 — configurar a senha administrativa

1. Na pasta `.streamlit`, copie `secrets.toml.example` e renomeie a cópia para `secrets.toml`.
2. Abra `secrets.toml` no Bloco de Notas. Ele já contém o ID da planilha correto. Defina uma senha forte no campo `password`:

   ```toml
   [google_sheets]
   spreadsheet_id = "1fuZYlIANUvqA0PpIhVENef_b9DMIGFhd4R_9M2Atjao"
   service_account_file = ".streamlit/google-service-account.json"

   [admin]
   password = "SUA_SENHA_FORTE_AQUI"
   ```
3. Salve. A senha administrativa é diferente da senha da conta Google. O arquivo `secrets.toml` está excluído do Git pela configuração `.gitignore`.

## Parte 3 — configurar deploy no Streamlit Community Cloud

O JSON da conta de serviço não deve ser enviado ao GitHub. No app publicado, abra **Manage app → Settings → Secrets** e adicione as configurações abaixo. Copie os valores da chave JSON da conta de serviço diretamente para o editor de Secrets:

```toml
[google_sheets]
spreadsheet_id = "1fuZYlIANUvqA0PpIhVENef_b9DMIGFhd4R_9M2Atjao"

[google_sheets.service_account]
type = "service_account"
project_id = "SEU_PROJECT_ID"
private_key_id = "SEU_PRIVATE_KEY_ID"
private_key = """-----BEGIN PRIVATE KEY-----
COLE_AQUI_A_CHAVE_PRIVADA_COMPLETA
-----END PRIVATE KEY-----
"""
client_email = "SUA_CONTA_DE_SERVICO@SEU_PROJECT.iam.gserviceaccount.com"
client_id = "SEU_CLIENT_ID"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "URL_DO_CERTIFICADO_DA_CONTA_DE_SERVICO"
universe_domain = "googleapis.com"

[admin]
password = "DEFINA_UMA_SENHA_ADMINISTRATIVA_FORTE"
```

Substitua cada exemplo pelo valor correspondente do JSON original, sem alterar os nomes dos campos. Em `private_key`, cole toda a chave incluindo `BEGIN PRIVATE KEY` e `END PRIVATE KEY`, no formato multilinha mostrado. Salve os Secrets e reinicie/reimplante o app. Não cole a chave no chat, no código ou em um commit. O endereço `client_email` deve ter permissão de **Editor** na planilha. Essa configuração também mantém o `spreadsheet_id` e a senha administrativa protegidos nos Secrets.

## Parte 4 — instalar e iniciar no VS Code Insiders

1. Extraia o ZIP para uma pasta simples, por exemplo `C:\Projetos\15BPM_PMRN_GoogleSheets`.
2. Abra essa pasta no VS Code Insiders em **File → Open Folder**.
3. Dê dois cliques em `1_INSTALAR_DEPENDENCIAS.bat` e aguarde a instalação terminar. É necessária conexão com a internet.
4. Depois que o JSON e `secrets.toml` estiverem configurados, execute `3_TESTAR_GOOGLE_SHEETS.bat`.
5. Execute `2_INICIAR_APP.bat`. O terminal mostrará um endereço local, normalmente `http://localhost:8501`; abra-o no navegador. O painel busca mudanças automaticamente a cada 15 segundos e após gravações feitas pelo próprio aplicativo.
6. Para interromper o app, volte à janela preta do terminal e pressione `Ctrl + C`.

## Abas esperadas da planilha

1. **Efetivo 15BPM** — criada/posicionada como primeira aba. Colunas: `ID`, `Função`, `Nome de Guerra`, `Ativo`, `Criado em`.
2. **Lançamentos** — uma linha por inclusão, com dados de data, companhia, subdivisão, quantidade, composição das equipes e tipos de OC.
3. **Tipos OC** — catálogo com `ID`, `Tipo de OC`, `Pontos`, `Ativo`, `Criado em`.

A inicialização não apaga as demais abas. Se já existir uma aba `Efetivo 15BPM`, ela será reutilizada. Caso contrário, uma nova aba será criada no início. A aba `Lançamentos` é a fonte de verdade dos lançamentos nesta versão.

## Observações de migração e segurança

- O aplicativo desta pasta não consulta mais o Supabase. Registros que estejam apenas no Supabase **não são copiados automaticamente** para o Google Sheets. Se esses dados de teste precisarem ser mantidos, exporte-os antes para CSV e faça a migração depois de validar o formato das colunas.
- Não publique o arquivo `google-service-account.json`, `secrets.toml` ou a aplicação com essas credenciais em repositório público. O `.gitignore` já exclui esses arquivos, mas confira o status do Git antes de enviar.
- A senha desta versão protege os formulários dentro da interface local; ela não substitui autenticação institucional robusta para hospedagem pública. Antes de compartilhar o app em rede ou hospedá-lo, é necessário rever autenticação, política de acesso e tratamento dos dados operacionais.
- Google Sheets funciona bem para protótipo e volumes modestos, mas não oferece as garantias transacionais de um banco de dados. Para uso operacional simultâneo por muitos usuários, vale planejar uma solução com autenticação institucional, trilha de auditoria e controle de concorrência.

## Correção v4

Esta versão corrige o erro `AttributeError: 'NoneType' object has no attribute 'get'` que ocorria ao abrir o formulário de novo lançamento, reforça a centralização do brasão na barra lateral e mantém a normalização dos nomes de guerra em maiúsculas com preservação de caracteres latinos acentuados e espaços. Para aplicar um patch sobre uma versão existente, use o ZIP incremental e preserve `.streamlit/secrets.toml` e `.streamlit/google-service-account.json`.

## Atualização v5 — painel e indicadores

A versão v5 apresenta a interface em letras maiúsculas, mantém a grafia UTF-8 com acentos, exibe pontos como números inteiros, formata percentuais com uma casa decimal (vírgula decimal), centraliza os cabeçalhos do painel e o rodapé institucional, remove a exportação CSV dos dados filtrados e conserva a exportação PDF. O painel apresenta três indicadores: Ocorrências, Ocorrências por tipo e Pontos das ocorrências.

## Ajustes atuais do painel

- O brasão fica centralizado na barra lateral; os filtros de período usam apenas `Data inicial` e `Data final`, aplicados aos dados exibidos.
- O painel inclui `% Pontos` junto aos indicadores e acumula a pontuação do mesmo efetivo no ranking e no gráfico `Efetivo x Pontos`.
- A tela administrativa lista os lançamentos com tipo de OC, pesquisa por data/equipe/tipo e ações de atualização e exclusão confirmada.
- Ao abrir o app, a mensagem de carregamento é `Carregando Aplicativo`; o rodapé identifica o aplicativo sem citar o armazenamento.

Para atualizar uma instalação existente, feche o Streamlit e substitua apenas `app.py`, `data_model.py` e `scoring.py` pela versão v5. Não substitua o arquivo `.streamlit/secrets.toml` nem `.streamlit/google-service-account.json`. Depois execute `3_TESTAR_GOOGLE_SHEETS.bat` e `2_INICIAR_APP.bat`.

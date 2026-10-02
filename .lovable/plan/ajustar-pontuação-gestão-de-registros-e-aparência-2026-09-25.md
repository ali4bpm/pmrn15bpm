# Ajustar pontuação, gestão de registros e aparência

## Implementação
- Tratar entorpecentes como faixas fixas: quantidades 1, 2, 3 e 4 correspondem, respectivamente, a 15, 20, 30 e 50 pontos, sem multiplicação adicional.
- Para munições, substituir a quantidade genérica por um campo para informar manualmente o número de munições; o aplicativo escolherá automaticamente a faixa e atribuirá 5, 10, 15, 20 ou 30 pontos.
- Manter o cálculo atual de quantidade × pontos unitários para as demais ocorrências.
- Exibir ações **Editar** e **Excluir** em cada registro somente para o administrador autenticado. A edição reutilizará o formulário, recalculará os pontos e salvará no mesmo registro; a exclusão pedirá confirmação.
- Autorizar no banco a edição apenas para a conta administrativa já definida, preservando as regras atuais de leitura, inclusão e exclusão.
- Alterar o aplicativo para modo claro e usar o brasão existente como marca-d’água desbotada no fundo do conteúdo, mantendo textos, tabelas e gráficos legíveis.

## Validação
- Conferir os cálculos das quatro faixas de entorpecentes e das cinco faixas de munição.
- Conferir abertura, salvamento e cancelamento da edição, além da confirmação de exclusão.
- Verificar a tela em computador e celular, incluindo contraste da marca-d’água.

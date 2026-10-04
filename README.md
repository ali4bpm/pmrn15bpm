# Produtividade 15º BPM PMRN

Titulo: "Produtividade 15º BPM PMRN"

This project was built with [Lovable](https://lovable.dev).

**Live app**: https://cipmrn10.lovable.app

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/95035496-3314-49f4-8985-d2dc070ee428).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```

## Conectar a um projeto Supabase externo

O arquivo `supabase/external-schema.sql` cria somente a estrutura necessária,
sem copiar registros do banco atual.

1. Crie um novo projeto em [Supabase](https://supabase.com/dashboard).
2. No SQL Editor do novo projeto, execute todo o conteúdo de
   `supabase/external-schema.sql`.
3. Em **Project Settings → API**, copie a URL do projeto e as chaves pública e
   secreta.
4. Atualize estas variáveis no ambiente onde o aplicativo será executado:

   - `VITE_SUPABASE_URL`: URL do novo projeto.
   - `VITE_SUPABASE_PUBLISHABLE_KEY`: chave pública/publishable.
   - `SUPABASE_URL`: a mesma URL do novo projeto.
   - `SUPABASE_PUBLISHABLE_KEY`: a mesma chave pública/publishable.
   - `SUPABASE_SERVICE_ROLE_KEY`: chave secreta/service role, disponível apenas
     no servidor.

5. Preserve também `ADMIN_ACCESS_PASSWORD` e `SESSION_SECRET` como segredos do
   servidor. Nunca use o prefixo `VITE_` na chave secreta/service role.

No Lovable, as variáveis gerenciadas da conexão atual não podem ser trocadas
manualmente por um projeto externo. Para usar este banco diretamente, exporte
o código e configure as variáveis acima no seu provedor de hospedagem.

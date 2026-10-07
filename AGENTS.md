<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.
<!-- LOVABLE:END -->

- Administrative productivity writes must use server functions protected by the encrypted shared-password session, because the password must never ship to the browser.
- External Supabase deployments use `supabase/external-schema.sql` as the canonical empty schema, because the managed Lovable Cloud connection remains platform-controlled.
- App data lives in the external Supabase project 15BPM_PMRN (hhkhpjgwtbradxblmiyp): browser reads via `src/integrations/supabase/external-client.ts` (publishable key), server writes via `externalAdmin()` in `src/lib/admin-gate.functions.ts` using the `EXTERNAL_SUPABASE_SERVICE_ROLE_KEY` secret, because the managed Lovable Cloud database is no longer used by the app.

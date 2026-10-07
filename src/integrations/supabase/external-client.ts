import { createClient } from "@supabase/supabase-js";

// Projeto Supabase externo: 15BPM_PMRN (hhkhpjgwtbradxblmiyp)
// A chave publishable é pública por natureza e pode ficar no código.
const EXTERNAL_SUPABASE_URL = "https://hhkhpjgwtbradxblmiyp.supabase.co";
const EXTERNAL_SUPABASE_PUBLISHABLE_KEY = "sb_publishable_awF2uDRG4_fd5sG_uYapyg_BaaDUoqI";

export const supabase = createClient(EXTERNAL_SUPABASE_URL, EXTERNAL_SUPABASE_PUBLISHABLE_KEY, {
  auth: {
    persistSession: false,
    autoRefreshToken: false,
  },
});

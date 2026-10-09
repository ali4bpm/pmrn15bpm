import { createHash, createHmac, timingSafeEqual } from "node:crypto";
import { createServerFn } from "@tanstack/react-start";
import { createClient } from "@supabase/supabase-js";
import { z } from "zod";

const EXTERNAL_SUPABASE_URL = "https://hhkhpjgwtbradxblmiyp.supabase.co";

function externalAdmin() {
  const serviceKey = process.env["EXTERNAL_SUPABASE_SERVICE_ROLE_KEY"];
  if (!serviceKey) throw new Error("EXTERNAL_SUPABASE_SERVICE_ROLE_KEY não configurado");
  return createClient(EXTERNAL_SUPABASE_URL, serviceKey, {
    auth: { persistSession: false, autoRefreshToken: false },
  });
}

const maxAgeMs = 1000 * 60 * 60 * 8;

const rowSchema = z.object({
  data: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  pelotao: z.string().min(1).max(100),
  localidade: z.string().min(1).max(120),
  efetivo: z.string().min(1).max(200),
  tipo_oc: z.string().min(1).max(500),
  qtde: z.number().int().positive(),
  pontos: z.number().nonnegative(),
});

function secret() {
  const s = process.env["SESSION_SECRET"];
  if (!s) throw new Error("SESSION_SECRET não configurado");
  return s;
}

function sign(payload: string) {
  return createHmac("sha256", secret()).update(payload).digest("hex");
}

function makeToken() {
  const exp = String(Date.now() + maxAgeMs);
  return `${exp}.${sign(exp)}`;
}

function tokenValid(token: string | undefined | null) {
  if (!token) return false;
  const [exp, sig] = token.split(".");
  if (!exp || !sig || Number(exp) < Date.now()) return false;
  const a = Buffer.from(sig, "hex");
  const b = Buffer.from(sign(exp), "hex");
  return a.length === b.length && timingSafeEqual(a, b);
}

function passwordMatches(input: string, expected: string) {
  const received = createHash("sha256").update(input, "utf8").digest();
  const stored = createHash("sha256").update(expected, "utf8").digest();
  return timingSafeEqual(received, stored);
}

function requireUnlocked(token: string) {
  if (!tokenValid(token)) throw new Error("Sessão expirada. Clique em \"Adicionar dados\" e informe a senha novamente.");
}

const tokenField = z.string().max(300);

export const getAdminGateStatus = createServerFn({ method: "POST" })
  .inputValidator((data) => z.object({ token: tokenField.nullable() }).parse(data))
  .handler(async ({ data }) => ({ unlocked: tokenValid(data.token) }));

export const unlockAdminData = createServerFn({ method: "POST" })
  .inputValidator((data) => z.object({ password: z.string().min(1).max(200) }).parse(data))
  .handler(async ({ data }) => {
    const expected = process.env["ADMIN_ACCESS_PASSWORD"];
    if (!expected) throw new Error("ADMIN_ACCESS_PASSWORD não configurado");
    if (!passwordMatches(data.password.trim(), expected)) return { ok: false as const, token: null };
    return { ok: true as const, token: makeToken() };
  });

export const saveProductivityRows = createServerFn({ method: "POST" })
  .inputValidator((data) => z.object({ token: tokenField, id: z.number().int().positive().nullable(), rows: z.array(rowSchema).min(1).max(40) }).parse(data))
  .handler(async ({ data }) => {
    requireUnlocked(data.token);
    const supabaseAdmin = externalAdmin();
    const firstRow = data.rows[0];
    if (!firstRow) throw new Error("Nenhum registro informado");
    const result = data.id
      ? await supabaseAdmin.from("produtividade").update(firstRow).eq("id", data.id)
      : await supabaseAdmin.from("produtividade").insert(data.rows);
    if (result.error) throw new Error(result.error.message);
    return { ok: true as const };
  });

export const deleteProductivityRow = createServerFn({ method: "POST" })
  .inputValidator((data) => z.object({ token: tokenField, id: z.number().int().positive() }).parse(data))
  .handler(async ({ data }) => {
    requireUnlocked(data.token);
    const supabaseAdmin = externalAdmin();
    const { error } = await supabaseAdmin.from("produtividade").delete().eq("id", data.id);
    if (error) throw new Error(error.message);
    return { ok: true as const };
  });
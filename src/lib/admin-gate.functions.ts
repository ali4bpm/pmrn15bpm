import { createHash, timingSafeEqual } from "node:crypto";
import { createServerFn } from "@tanstack/react-start";
import { useSession } from "@tanstack/react-start/server";
import { z } from "zod";

const sessionName = "admin-data-gate";
const maxAge = 60 * 60 * 8;

type AdminGateSession = { unlocked?: boolean };

const rowSchema = z.object({
  data: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  pelotao: z.string().min(1).max(100),
  localidade: z.string().min(1).max(120),
  efetivo: z.string().min(1).max(200),
  tipo_oc: z.string().min(1).max(500),
  qtde: z.number().int().positive(),
  pontos: z.number().nonnegative(),
});

function sessionConfig() {
  const password = process.env["SESSION_SECRET"];
  if (!password) throw new Error("SESSION_SECRET não configurado");
  return {
    password,
    name: sessionName,
    maxAge,
    cookie: { httpOnly: true, secure: true, sameSite: "lax" as const, path: "/" },
  };
}

function passwordMatches(input: string, expected: string) {
  const received = createHash("sha256").update(input, "utf8").digest();
  const stored = createHash("sha256").update(expected, "utf8").digest();
  return timingSafeEqual(received, stored);
}

async function requireUnlocked() {
  const session = await useSession<AdminGateSession>(sessionConfig());
  if (!session.data.unlocked) throw new Error("Acesso não autorizado");
}

export const getAdminGateStatus = createServerFn({ method: "GET" }).handler(async () => {
  const session = await useSession<AdminGateSession>(sessionConfig());
  return { unlocked: session.data.unlocked === true };
});

export const unlockAdminData = createServerFn({ method: "POST" })
  .inputValidator((data) => z.object({ password: z.string().min(1).max(200) }).parse(data))
  .handler(async ({ data }) => {
    const expected = process.env["ADMIN_ACCESS_PASSWORD"];
    if (!expected) throw new Error("ADMIN_ACCESS_PASSWORD não configurado");
    if (!passwordMatches(data.password, expected)) return { ok: false as const };
    const session = await useSession<AdminGateSession>(sessionConfig());
    await session.update({ unlocked: true });
    return { ok: true as const };
  });

export const saveProductivityRows = createServerFn({ method: "POST" })
  .inputValidator((data) => z.object({ id: z.number().int().positive().nullable(), rows: z.array(rowSchema).min(1).max(40) }).parse(data))
  .handler(async ({ data }) => {
    await requireUnlocked();
    const { supabaseAdmin } = await import("@/integrations/supabase/client.server");
    const result = data.id
      ? await supabaseAdmin.from("produtividade").update(data.rows[0]).eq("id", data.id)
      : await supabaseAdmin.from("produtividade").insert(data.rows);
    if (result.error) throw new Error(result.error.message);
    return { ok: true as const };
  });

export const deleteProductivityRow = createServerFn({ method: "POST" })
  .inputValidator((data) => z.object({ id: z.number().int().positive() }).parse(data))
  .handler(async ({ data }) => {
    await requireUnlocked();
    const { supabaseAdmin } = await import("@/integrations/supabase/client.server");
    const { error } = await supabaseAdmin.from("produtividade").delete().eq("id", data.id);
    if (error) throw new Error(error.message);
    return { ok: true as const };
  });
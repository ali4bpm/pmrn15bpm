import { createFileRoute } from "@tanstack/react-router";
import { useServerFn } from "@tanstack/react-start";
import { PanelLeftClose, PanelLeftOpen, Pencil, Plus, Trash2, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, LabelList } from "recharts";
import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";
import { supabase } from "@/integrations/supabase/client";
import brasao from "@/assets/brasao-15-bpm.png.asset.json";
import { Button } from "@/components/ui/button";
import { deleteProductivityRow, getAdminGateStatus, saveProductivityRows, unlockAdminData } from "@/lib/admin-gate.functions";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Produtividade e Pontuação 15º BPM PMRN" },
      { name: "description", content: "Painel de produtividade e pontuação do efetivo do 15º BPM PMRN: registros, ranking, distribuição por companhias e relatórios em PDF." },
      { property: "og:title", content: "Produtividade e Pontuação 15º BPM PMRN" },
      { property: "og:description", content: "Ranking de produtividade, distribuição por companhias e relatórios do 15º BPM PMRN." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: Index,
});

const OCORRENCIAS: [string, number][] = [
  ["ARMA BRANCA (Homicídio, Tentativa de homicídio com Lesão Corporal Grave e Roubo consumado)", 5],
  ["ARTESANAL CURTA", 20],
  ["ARTESANAL LONGA", 25],
  ["COLETE BALÍSTICO", 20],
  ["ESPINGARDA", 35],
  ["METRALHADORA", 80],
  ["FUZIL", 100],
  ["PISTOLA", 40],
  ["REVÓLVER", 30],
  ["RIFLE", 35],
  ["SIMULACRO", 6],
  ["ENTORPECENTE De 1g a 500g - Peso 1 (Duas ou mais Ocorrências no mesmo dia até o total contará como pontuação subsequente)", 15],
  ["ENTORPECENTE De 500g a 2kg - Peso 2 (Duas ou mais Ocorrências no mesmo dia até o total contará como pontuação subsequente)", 20],
  ["ENTORPECENTE De 2kg a 10kg - Peso 3 (Duas ou mais Ocorrências no mesmo dia até o total contará como pontuação subsequente)", 30],
  ["ENTORPECENTE Acima de 10kg - Peso 4", 50],
  ["ARROMBAMENTO", 6],
  ["ESTELIONATO", 7],
  ["FURTO", 6],
  ["RECEPTAÇÃO", 8],
  ["ROUBO", 12],
  ["MUNIÇÃO 1 - 10", 5],
  ["MUNIÇÃO 11 - 20", 10],
  ["MUNIÇÃO 21 - 50", 15],
  ["MUNIÇÃO 51 - 100", 20],
  ["MUNIÇÃO 101 ou mais", 30],
  ["FORAGIDO", 10],
  ["VEÍCULO ABANDONADO", 6],
  ["VEÍCULO (FURTO/ROUBO) APREENDIDO (Apenas veículos com queixa de furto/roubo/adulterado ou usados para crimes como: Homicídios, roubos e transportes de entorpecentes)", 7],
  ["TCO/BOC 4º BPM", 6],
  ["TCO/BOC DELEGACIA", 3],
  ["BOPPM (Oc's como: Isolamento local de crime, ameaça, perturbação sossego alheio, etc..)", 3],
  ["VIOLÊNCIA DOMÉSTICA", 5],
  ["ESTUPRO (Com flagrante, vítima, acusado e materialidade)", 30],
  ["HOMICÍDIO COM PRISÃO EM FLAGRANTE (Apenas para homicídios consumados)", 50],
];
const PTS = Object.fromEntries(OCORRENCIAS);
const ENTORPECENTES_QTDE: Record<string, number> = {
  "ENTORPECENTE De 1g a 500g - Peso 1 (Duas ou mais Ocorrências no mesmo dia até o total contará como pontuação subsequente)": 1,
  "ENTORPECENTE De 500g a 2kg - Peso 2 (Duas ou mais Ocorrências no mesmo dia até o total contará como pontuação subsequente)": 2,
  "ENTORPECENTE De 2kg a 10kg - Peso 3 (Duas ou mais Ocorrências no mesmo dia até o total contará como pontuação subsequente)": 3,
  "ENTORPECENTE Acima de 10kg - Peso 4": 4,
};
const isMunicao = (tipo: string) => tipo.startsWith("MUNIÇÃO ");
const tipoMunicao = (qtde: number) => qtde <= 10 ? "MUNIÇÃO 1 - 10" : qtde <= 20 ? "MUNIÇÃO 11 - 20" : qtde <= 50 ? "MUNIÇÃO 21 - 50" : qtde <= 100 ? "MUNIÇÃO 51 - 100" : "MUNIÇÃO 101 ou mais";
const MUNICAO_MIN: Record<string, number> = { "MUNIÇÃO 1 - 10": 1, "MUNIÇÃO 11 - 20": 11, "MUNIÇÃO 21 - 50": 21, "MUNIÇÃO 51 - 100": 51, "MUNIÇÃO 101 ou mais": 101 };
const calcularPontos = (tipo: string, qtde: number) => {
  if (ENTORPECENTES_QTDE[tipo]) return PTS[tipo] ?? 0;
  if (isMunicao(tipo)) return PTS[tipoMunicao(qtde)] ?? 0;
  return qtde * (PTS[tipo] ?? 0);
};
const MESES = ["Todos", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"];
const CORES = ["var(--primary)", "var(--accent)", "var(--destructive)", "#3949ab", "#2e7d32", "#c9a227", "#6b7280"];
const COMPANHIAS = ["1ª CPM/Sede Santa Cruz", "2ª CPM/Sede Tangará", "3ª CPM/Sede Santa Cruz"];
const subdivOf = (p: string) => SUBDIVISOES[p] ?? [];
const SUBDIVISOES: Record<string, string[]> = {
  "1ª CPM/Sede Santa Cruz": ["1º Pelotão — Santa Cruz", "DPM de Campo Redondo", "DPM de Lajes Pintadas"],
  "2ª CPM/Sede Tangará": ["1º Pelotão — Tangará", "DPM de Sítio Novo", "DPM de Serra Caiada", "DPM de Boa Saúde", "DPM de Sen. Elói de Souza"],
  "3ª CPM/Sede Santa Cruz": ["1º Pelotão — Jaçanã", "DPM de Cel. Ezequiel", "DPM de Japi", "DPM de São Bento do Trairi"],
};

const normEfetivo = (s: string) => s.trim().replace(/\s+/g, " ").replace(/°/g, "º").toLocaleUpperCase("pt-BR");
type Row = { id: number; data: string; pelotao: string; localidade: string | null; efetivo: string; tipo_oc: string; qtde: number; pontos: number };
const fmtData = (d: string) => d.split("-").reverse().join("/");
const uniq = (a: string[]) => Array.from(new Set(a)).sort((x, y) => x.localeCompare(y));

function gerarPdf(titulo: string, sub: string, head: string[], body: (string | number)[][], arquivo: string) {
  const doc = new jsPDF({ orientation: "landscape", unit: "mm", format: "a4" });
  doc.setFontSize(16); doc.text("15º BPM PMRN", 148, 14, { align: "center" });
  doc.setFontSize(12); doc.text(titulo, 10, 24);
  doc.setFontSize(9); doc.text(sub, 10, 30);
  autoTable(doc, {
    startY: 35, head: [head], body: body.length ? body : [["Sem registros", ...head.slice(1).map(() => "")]],
    styles: { fontSize: 7.5 }, headStyles: { fillColor: [57, 73, 171] }, alternateRowStyles: { fillColor: [243, 244, 246] },
  });
  const y = (doc as unknown as { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 8;
  doc.text("15º BPM - PMRN", 10, y);
  doc.save(arquivo);
}

const inputCls = "w-full rounded-md border bg-background px-3 py-2 text-sm";

function MultiCheck({ label, options, selected, onChange }: { label: string; options: string[]; selected: string[]; onChange: (v: string[]) => void }) {
  const [open, setOpen] = useState(false);
  const toggle = (o: string) => onChange(selected.includes(o) ? selected.filter((x) => x !== o) : [...selected, o]);
  return (
    <div>
      <button type="button" onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between rounded-md border bg-background px-3 py-2 text-left text-sm">
        <span className="text-xs font-medium text-muted-foreground">{label}{selected.length ? ` (${selected.length})` : ""}</span>
        <span aria-hidden="true" className="text-xs">{open ? "▲" : "▼"}</span>
      </button>
      {open && options.length > 0 && (
        <div className="thin-scrollbar mt-1 max-h-44 overflow-y-auto rounded-md border bg-background p-2">
          {options.map((o) => (
            <label key={o} className="flex items-start gap-2 py-0.5 text-xs">
              <input type="checkbox" className="accent-[#394391] mt-0.5" checked={selected.includes(o)} onChange={() => toggle(o)} />
              <span className="break-all">{o}</span>
            </label>
          ))}
        </div>
      )}
      {open && options.length === 0 && <p className="mt-1 text-xs text-muted-foreground">Nenhuma opção disponível.</p>}
    </div>
  );
}

function Index() {
  const [rows, setRows] = useState<Row[]>([]);
  const [erro, setErro] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [f, setF] = useState({ ano: "Todos", mes: "Todos", pelotao: "Todos", localidade: "Todos", efetivo: [] as string[], efetivoTexto: "", tipo: [] as string[] });
  const [asideOpen, setAsideOpen] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editando, setEditando] = useState<Row | null>(null);
  const gateStatus = useServerFn(getAdminGateStatus);
  const deleteRow = useServerFn(deleteProductivityRow);

  const carregar = async () => {
      const { data, error } = await supabase.from("produtividade").select("id,data,pelotao,localidade,efetivo,tipo_oc,qtde,pontos").order("data", { ascending: false });
    if (error) setErro(error.message); else { setErro(null); setRows((data ?? []).map((r) => ({ ...r, pontos: Number(r.pontos) }))); }
  };
  useEffect(() => {
    carregar();
    gateStatus().then(({ unlocked }) => setIsAdmin(unlocked)).catch(() => setIsAdmin(false));
  }, []);
  const abrirInclusao = () => { setEditando(null); setModalOpen(true); };
  const fecharModal = () => { setModalOpen(false); void carregar(); };
  const abrirEdicao = (row: Row) => { setEditando(row); setModalOpen(true); };
  const excluir = async (row: Row) => {
    if (!window.confirm(`Excluir o registro de ${row.efetivo} em ${fmtData(row.data)}?`)) return;
    try { await deleteRow({ data: { id: row.id } }); await carregar(); }
    catch (error) { setErro(`Não foi possível excluir o registro: ${error instanceof Error ? error.message : "erro inesperado"}`); }
  };

  const anos = uniq(rows.map((r) => r.data.slice(0, 4))).reverse();
  const pelotoes = uniq([...COMPANHIAS, ...rows.map((r) => r.pelotao)]);
  const localidades = uniq(rows.map((r) => r.localidade ?? "").filter(Boolean));
  const efetivos = uniq(rows.map((r) => normEfetivo(r.efetivo)));
  const tipos = rows.length ? uniq(rows.map((r) => r.tipo_oc)) : OCORRENCIAS.map((o) => o[0]);

  const df = useMemo(() => rows.filter((r) =>
    (f.ano === "Todos" || r.data.startsWith(f.ano)) &&
    (f.mes === "Todos" || Number(r.data.slice(5, 7)) === MESES.indexOf(f.mes)) &&
    (f.pelotao === "Todos" || r.pelotao === f.pelotao) &&
    (f.localidade === "Todos" || r.localidade === f.localidade) &&
    (f.efetivo.length === 0 || f.efetivo.includes(normEfetivo(r.efetivo))) &&
    (!f.efetivoTexto.trim() || normEfetivo(r.efetivo).includes(normEfetivo(f.efetivoTexto))) &&
    (f.tipo.length === 0 || f.tipo.includes(r.tipo_oc))), [rows, f]);

  const dist = useMemo(() => {
    const m = new Map<string, number>();
    df.forEach((r) => m.set(r.pelotao, (m.get(r.pelotao) ?? 0) + (Number(r.qtde) || 0)));
    const total = [...m.values()].reduce((a, b) => a + b, 0) || 1;
    return [...m].map(([name, qtde]) => ({ name, qtde, value: qtde, pct: (qtde / total) * 100 }));
  }, [df]);

  const distLoc = useMemo(() => {
    const m = new Map<string, { qtde: number; pontos: number }>();
    df.forEach((r) => {
      const loc = r.localidade ?? "—";
      const c = m.get(loc) ?? { qtde: 0, pontos: 0 };
      c.qtde += Number(r.qtde) || 0; c.pontos += Number(r.pontos) || 0; m.set(loc, c);
    });
    const total = [...m.values()].reduce((a, b) => a + b.qtde, 0) || 1;
    return COMPANHIAS.flatMap((p) =>
      subdivOf(p)
        .filter((s) => m.has(s))
        .map((s) => ({ name: s, pelotao: p, value: m.get(s)!.qtde, qtde: m.get(s)!.qtde, pontos: m.get(s)!.pontos, pct: (m.get(s)!.qtde / total) * 100 })),
    );
  }, [df]);

  const ranking = useMemo(() => {
    const m = new Map<string, { efetivo: string; pels: Set<string>; locs: Set<string>; qtde: number; pontos: number }>();
    df.forEach((r) => {
      const nome = normEfetivo(r.efetivo);
      const c = m.get(nome) ?? { efetivo: nome, pels: new Set<string>(), locs: new Set<string>(), qtde: 0, pontos: 0 };
      c.pels.add(r.pelotao); c.locs.add(r.localidade ?? "—");
      c.qtde += Number(r.qtde) || 0; c.pontos += Number(r.pontos) || 0; m.set(nome, c);
    });
    return [...m.values()]
      .map((c) => ({ efetivo: c.efetivo, rotulo: c.efetivo, pelotao: [...c.pels].join(", "), localidade: [...c.locs].join(", "), qtde: c.qtde, pontos: c.pontos }))
      .sort((a, b) => b.pontos - a.pontos || b.qtde - a.qtde);
  }, [df]);

  const filtroTxt = `Ano: ${f.ano} | Mês: ${f.mes} | Companhia: ${f.pelotao} | Subdivisão: ${f.localidade} | Efetivo: ${f.efetivoTexto.trim() ? f.efetivoTexto : f.efetivo.length ? f.efetivo.join(", ") : "Todos"} | Tipo de OC: ${f.tipo.length ? f.tipo.join(", ") : "Todos"}`;
  const limparFiltros = () => setF({ ano: "Todos", mes: "Todos", pelotao: "Todos", localidade: "Todos", efetivo: [], efetivoTexto: "", tipo: [] });
  const sel = (label: string, key: keyof typeof f, opts: string[]) => (
    <label className="block text-xs font-medium text-muted-foreground">
      {label}
      <select className={`${inputCls} mt-1 text-foreground`} value={f[key]} onChange={(e) => setF({ ...f, [key]: e.target.value })}>
        {["Todos", ...opts.filter((o) => o !== "Todos")].map((o) => <option key={o}>{o}</option>)}
      </select>
    </label>
  );

  return (
    <div className="relative min-h-screen bg-background text-foreground lg:flex">
      <img src={brasao.url} alt="" aria-hidden="true" className="pointer-events-none fixed left-1/2 top-1/2 z-0 w-[min(72vw,680px)] -translate-x-1/2 -translate-y-1/2 opacity-[0.16]" />
      {asideOpen && (
      <aside className="border-b bg-card p-5 lg:sticky lg:top-0 lg:h-screen lg:w-72 lg:shrink-0 lg:overflow-y-auto lg:border-b-0 lg:border-r">
        <p className="text-center text-xl font-extrabold">15º BPM PMRN</p>
        <img src={brasao.url} alt="Brasão do 15º BPM" className="mx-auto my-4 max-h-56 object-contain" />
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider">Filtros</h2>
        <div className="space-y-3">
          {sel("Ano", "ano", anos)}
          {sel("Mês", "mes", MESES)}
          {sel("Companhias", "pelotao", pelotoes)}
          {sel("Subdivisão", "localidade", localidades)}
          <label className="block text-xs font-medium text-muted-foreground">
            Efetivo
            <input className={`${inputCls} mt-1 text-foreground`} placeholder="Todos" value={f.efetivoTexto}
              onChange={(e) => setF({ ...f, efetivoTexto: e.target.value.toLocaleUpperCase("pt-BR") })} />
          </label>
          <MultiCheck label="Selecionar Efetivo(s)" options={efetivos} selected={f.efetivo} onChange={(v) => setF({ ...f, efetivo: v })} />
          <MultiCheck label="Tipo de Ocorrência" options={tipos} selected={f.tipo} onChange={(v) => setF({ ...f, tipo: v })} />
          <button className="w-full rounded-md border bg-secondary px-3 py-2 text-sm font-medium hover:bg-secondary/70" onClick={limparFiltros}>
            Limpar filtros
          </button>
        </div>
      </aside>
      )}

      <div className="relative z-[1] min-w-0 flex-1">
        <div className="sticky top-0 z-10 flex items-center justify-between gap-2 border-b bg-background/95 px-3 py-2">
          <button type="button" aria-label={asideOpen ? "Ocultar filtros" : "Mostrar filtros"}
            className="inline-flex items-center gap-2 rounded-md border bg-card px-3 py-1.5 text-sm font-medium hover:bg-muted/50"
            onClick={() => setAsideOpen((o) => !o)}>
            {asideOpen ? <PanelLeftClose className="h-4 w-4" /> : <PanelLeftOpen className="h-4 w-4" />}
            <span>{asideOpen ? "Ocultar filtros" : "Mostrar filtros"}</span>
          </button>
          <Button type="button" size="sm" onClick={abrirInclusao}>
            <Plus className="h-4 w-4" />
            Adicionar dados
          </Button>
        </div>
        <main className="mx-auto w-full max-w-6xl space-y-6 p-5 lg:p-8">
        <h1 className="text-center text-3xl font-extrabold">Produtividade e Pontuação 15º BPM PMRN</h1>

        <details className="rounded-lg border bg-card p-4">
          <summary className="cursor-pointer font-semibold">Sobre o Aplicativo</summary>
          <p className="mt-3 text-sm">Este aplicativo foi desenvolvido para mostrar a produtividade e pontuação do efetivo do 15º BPM - PMRN, baseado nas Categorias, Critérios e Pontos elencados abaixo:</p>
          <ul className="mt-2 space-y-1 text-sm">
            {OCORRENCIAS.map(([n, p]) => <li key={n}>{n}: {String(p).padStart(2, "0")} pontos</li>)}
          </ul>
        </details>

                {erro && <p className="rounded-md border border-destructive p-3 text-sm text-destructive">Erro ao carregar dados: {erro}</p>}

        <section className="rounded-lg border bg-card p-4">
          <h2 className="mb-3 text-lg font-semibold">Dados filtrados</h2>
          <div className="thin-scrollbar max-h-96 overflow-auto rounded-md border border-border/60">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-card text-left text-xs uppercase text-muted-foreground">
                <tr>{["Data", "Companhia", "Subdivisão", "Efetivo", "Tipo de OC", "Qtde", "Pontos"].map((h) => <th key={h} className="border-b p-2">{h}</th>)}</tr>
              </thead>
              <tbody>
                {df.map((r) => (
                  <tr key={r.id} className="border-b last:border-0">
                    <td className="p-2">{fmtData(r.data)}</td><td className="p-2">{r.pelotao}</td><td className="p-2">{r.localidade ?? "—"}</td><td className="p-2">{r.efetivo}</td>
                    <td className="p-2">{r.tipo_oc}</td><td className="p-2 text-right">{r.qtde}</td><td className="p-2 text-right">{r.pontos}</td>
                  </tr>
                ))}
                {!df.length && <tr><td colSpan={7} className="p-4 text-center text-muted-foreground">Sem registros</td></tr>}
              </tbody>
            </table>
          </div>
          <button className="mt-4 w-full rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
            onClick={() => gerarPdf("Resumo - Tipos filtrados", filtroTxt, ["Data", "Companhia", "Subdivisão", "Efetivo", "Tipo de OC", "Qtde", "Pontos"],
              df.map((r) => [fmtData(r.data), r.pelotao, r.localidade ?? "—", r.efetivo, r.tipo_oc, r.qtde, r.pontos]), "resumo_15_bpm.pdf")}>
            Download em PDF - Resumo
          </button>
        </section>

        <section className="rounded-lg border bg-card p-4">
          <h2 className="mb-3 text-center text-lg font-semibold">Distribuição de Ocorrências por Companhia</h2>
          {dist.length ? (
            <div className="mx-auto w-full max-w-2xl">
              <div className="h-72">
                <ResponsiveContainer>
                  <PieChart>
                    <Pie data={dist} dataKey="value" nameKey="name" innerRadius="35%" label={(e) => `${e.name} ${e.pct.toFixed(1)}%`}>
                      {dist.map((_, i) => <Cell key={i} fill={CORES[i % CORES.length]} />)}
                    </Pie>
                    <Tooltip formatter={(v: number) => `${v} pts`} />

                  </PieChart>
                </ResponsiveContainer>
              </div>
              <table className="mt-4 w-full text-center text-sm">
                <thead className="text-xs uppercase text-muted-foreground"><tr><th className="border-b p-2">Companhia</th><th className="border-b p-2">Qtde</th><th className="border-b p-2">Porcentagem de Ocorrências</th></tr></thead>
                <tbody>{dist.map((d) => <tr key={d.name}><td className="p-2">{d.name}</td><td className="p-2">{d.qtde}</td><td className="p-2">{d.pct.toFixed(2)}%</td></tr>)}</tbody>
              </table>
            </div>
          ) : <p className="text-sm text-muted-foreground">Sem dados para a distribuição por Companhia.</p>}

          {distLoc.length > 0 && (
            <div className="mt-6 border-t pt-4">
              <h3 className="mb-3 text-center text-base font-semibold">Distribuição de Ocorrências por Subdivisão</h3>
              <div className="mx-auto w-full max-w-3xl">
                <div className="h-72">
                  <ResponsiveContainer>
                    <PieChart>
                      <Pie data={distLoc} dataKey="value" nameKey="name" innerRadius="35%" label={(e) => `${e.name} ${e.pct.toFixed(1)}%`}>
                        {distLoc.map((_, i) => <Cell key={i} fill={CORES[i % CORES.length]} />)}
                      </Pie>
                      <Tooltip formatter={(v: number) => `${v} pts`} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <table className="mt-4 w-full text-center text-sm">
                  <thead className="text-xs uppercase text-muted-foreground">
                    <tr><th className="border-b p-2">Companhia</th><th className="border-b p-2">Subdivisão</th><th className="border-b p-2">Qtde</th><th className="border-b p-2">Porcentagem de Ocorrências</th></tr>
                  </thead>
                  <tbody>
                    {distLoc.map((d) => (
                      <tr key={d.name} className="border-b last:border-0">
                        <td className="p-2">{d.pelotao}</td><td className="p-2">{d.name}</td>
                        <td className="p-2">{d.qtde}</td><td className="p-2">{d.pct.toFixed(2)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </section>

        <section className="rounded-lg border bg-card p-4">
          <h2 className="mb-3 text-lg font-semibold">Ranking de Produtividade</h2>
          <div className="max-h-96 overflow-auto rounded-md border border-border/60 thin-scrollbar">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-card text-left text-xs uppercase text-muted-foreground">
                <tr>{["#", "Efetivo", "Companhia", "Subdivisão", "Qtde", "Pontos"].map((h) => <th key={h} className="border-b p-2">{h}</th>)}</tr>
              </thead>
              <tbody>
                {ranking.map((r, i) => (
                  <tr key={r.rotulo + r.pelotao} className="border-b last:border-0">
                    <td className="p-2 font-semibold">{i + 1}</td><td className="p-2">{r.efetivo}</td><td className="p-2">{r.pelotao}</td><td className="p-2">{r.localidade}</td>
                    <td className="p-2 text-right">{r.qtde}</td><td className="p-2 text-right font-semibold">{r.pontos}</td>
                  </tr>
                ))}
                {!ranking.length && <tr><td colSpan={6} className="p-4 text-center text-muted-foreground">Sem registros</td></tr>}
              </tbody>
            </table>
          </div>
          <button className="mt-4 w-full rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
            onClick={() => gerarPdf("Ranking de Produtividade", filtroTxt, ["Efetivo", "Companhia", "Subdivisão", "Qtde", "Pontos"],
              ranking.map((r) => [r.efetivo, r.pelotao, r.localidade, r.qtde, r.pontos]), "ranking_produtividade_15_bpm.pdf")}>
            Download em PDF - Ranking
          </button>
        </section>

        <section className="rounded-lg border bg-card p-4">
          <h2 className="mb-3 text-lg font-semibold">Efetivo x Pontos</h2>
          {ranking.length ? (
            <div className="thin-scrollbar max-h-96 overflow-y-auto" style={{ scrollbarGutter: "stable" }}>
              <div style={{ height: Math.max(220, ranking.length * 36) }}>

              <ResponsiveContainer>
                <BarChart data={ranking} layout="vertical" margin={{ left: 10, right: 50 }}>
                  <XAxis type="number" stroke="var(--muted-foreground)" tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="rotulo" width={220} interval={0} tick={{ fontSize: 10 }} stroke="var(--muted-foreground)" />
                  <Tooltip />
                  <Bar dataKey="pontos" name="Pontos" fill="var(--primary)" radius={[0, 4, 4, 0]}>
                    <LabelList dataKey="pontos" position="right" fill="var(--foreground)" fontSize={9} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              </div>
            </div>

          ) : <p className="text-sm text-muted-foreground">Sem dados para o gráfico de produtividade.</p>}
        </section>

        <footer className="pt-6 text-center text-sm text-muted-foreground">Aplicativo desenvolvido para o 15º BPM - PMRN</footer>
        </main>
      </div>

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 p-4" onClick={fecharModal}>
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg border bg-card p-5" onClick={(e) => e.stopPropagation()}>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold">{editando ? "Editar registro" : "Adicionar dados"}</h2>
              <button type="button" aria-label="Fechar" className="rounded-md p-1 hover:bg-muted/50" onClick={fecharModal}>
                <X className="h-5 w-5" />
              </button>
            </div>
            {isAdmin ? (
              <>
                <FormInclusao key={editando?.id ?? "novo"} registro={editando} onSaved={async () => { await carregar(); setEditando(null); setModalOpen(false); }} />
                {editando && <button type="button" className="mt-2 text-sm underline" onClick={() => setEditando(null)}>Cancelar edição</button>}
                <h3 className="mb-2 mt-6 text-sm font-semibold">Registros adicionados</h3>
                <div className="thin-scrollbar max-h-72 overflow-auto rounded-md border border-border/60">
                  <table className="w-full text-xs">
                    <thead className="sticky top-0 bg-card text-left uppercase text-muted-foreground">
                      <tr>{["Data", "Efetivo", "Tipo de OC", "Pontos", "Ações"].map((h) => <th key={h} className="border-b p-2">{h}</th>)}</tr>
                    </thead>
                    <tbody>
                      {df.map((r) => (
                        <tr key={r.id} className={`border-b last:border-0 ${editando?.id === r.id ? "bg-muted/50" : ""}`}>
                          <td className="p-2">{fmtData(r.data)}</td><td className="p-2">{r.efetivo}</td><td className="p-2">{r.tipo_oc}</td><td className="p-2 text-right">{r.pontos}</td>
                          <td className="p-2"><div className="flex justify-end gap-1">
                            <Button type="button" size="icon" variant="ghost" aria-label="Editar registro" title="Editar" onClick={() => abrirEdicao(r)}><Pencil className="h-4 w-4" /></Button>
                            <Button type="button" size="icon" variant="ghost" aria-label="Excluir registro" title="Excluir" className="text-destructive hover:text-destructive" onClick={() => excluir(r)}><Trash2 className="h-4 w-4" /></Button>
                          </div></td>
                        </tr>
                      ))}
                      {!df.length && <tr><td colSpan={5} className="p-4 text-center text-muted-foreground">Sem registros</td></tr>}
                    </tbody>
                  </table>
                </div>
              </>
            ) : <Login onUnlocked={() => setIsAdmin(true)} />}
          </div>
        </div>
      )}
    </div>
  );
}

function Login({ onUnlocked }: { onUnlocked: () => void }) {
  const [senha, setSenha] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const unlock = useServerFn(unlockAdminData);
  const entrar = async () => {
    try {
      const result = await unlock({ data: { password: senha } });
      if (result.ok) onUnlocked(); else setMsg("Senha inválida.");
    } catch { setMsg("Não foi possível validar a senha."); }
  };
  return (
    <div className="mx-auto max-w-md space-y-3">
      <label className="block text-xs font-medium text-muted-foreground">Senha de acesso
        <input className={`${inputCls} mt-1`} type="password" value={senha} onChange={(e) => setSenha(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") void entrar(); }} placeholder="Digite a senha" autoFocus />
      </label>
      <Button className="w-full" onClick={entrar}>Entrar</Button>
      {msg && <p className="text-sm text-muted-foreground">{msg}</p>}
    </div>
  );
}

function FormInclusao({ registro, onSaved }: { registro: Row | null; onSaved: () => void | Promise<void> }) {
  const defaultCompanhia = COMPANHIAS[0] ?? "";
  const [data, setData] = useState(registro?.data ?? new Date().toISOString().slice(0, 10));
  const [pelotao, setPelotao] = useState<string>(registro?.pelotao ?? defaultCompanhia);
  const [localidade, setLocalidade] = useState<string>(registro?.localidade ?? subdivOf(registro?.pelotao ?? defaultCompanhia)[0] ?? "");
  const [efetivo, setEfetivo] = useState(registro?.efetivo ?? "");
  const [tiposSel, setTiposSel] = useState<string[]>(registro ? [registro.tipo_oc] : []);
  const [qtde, setQtde] = useState(registro && !ENTORPECENTES_QTDE[registro.tipo_oc] && !isMunicao(registro.tipo_oc) ? registro.qtde : 1);
  const [municoes, setMunicoes] = useState(registro && isMunicao(registro.tipo_oc) ? (MUNICAO_MIN[registro.tipo_oc] ?? 1) : 1);
  const [msg, setMsg] = useState<string | null>(null);
  const saveRows = useServerFn(saveProductivityRows);
  const temMunicao = tiposSel.some(isMunicao);
  const comum = tiposSel.filter((t) => !isMunicao(t) && !ENTORPECENTES_QTDE[t]);
  const soEntorpecente = tiposSel.length > 0 && comum.length === 0 && !temMunicao;
  const linhaPontos = (t: string) => calcularPontos(t, isMunicao(t) ? municoes : qtde);
  const totalPontos = tiposSel.reduce((s, t) => s + linhaPontos(t), 0);
  const trocarPelotao = (p: string) => { setPelotao(p); setLocalidade(subdivOf(p)[0] ?? ""); };
  const toggleTipos = (v: string[]) => {
    const nova = v.find((x) => !tiposSel.includes(x));
    if (nova && isMunicao(nova)) setMunicoes(MUNICAO_MIN[nova] ?? 1);
    setTiposSel(v);
  };
  const trocarQtde = (valor: number) => setQtde(Math.max(1, valor || 1));
  const trocarMunicoes = (valor: number) => setMunicoes(Math.max(1, valor || 1));
  const salvar = async () => {
    if (!efetivo.trim()) return setMsg("Preencha o Efetivo.");
    if (!tiposSel.length) return setMsg("Selecione pelo menos um Tipo de OC.");
    const linhas = Array.from(new Set(tiposSel.map((t) => (isMunicao(t) ? tipoMunicao(municoes) : t)))).map((t) => ({
      data, pelotao, localidade, efetivo: normEfetivo(efetivo), tipo_oc: t,
      qtde: isMunicao(t) || ENTORPECENTES_QTDE[t] ? 1 : qtde,
      pontos: calcularPontos(t, isMunicao(t) ? municoes : qtde),
    }));
    try { await saveRows({ data: { id: registro?.id ?? null, rows: linhas } }); await onSaved(); }
    catch (error) { setMsg(`Não foi possível salvar o registro: ${error instanceof Error ? error.message : "erro inesperado"}`); }
  };
  return (
    <div className="space-y-4">
      <p className="text-sm text-primary">Usuário autenticado. Você pode adicionar registros.</p>
      <div className="grid gap-3 md:grid-cols-3">
        <label className="text-xs">Data<input type="date" className={`${inputCls} mt-1`} value={data} onChange={(e) => setData(e.target.value)} /></label>
        <label className="text-xs">Companhia
          <select className={`${inputCls} mt-1`} value={pelotao} onChange={(e) => trocarPelotao(e.target.value)}>
            {COMPANHIAS.map((p) => <option key={p}>{p}</option>)}
          </select></label>
        <label className="text-xs">Subdivisão
          <select className={`${inputCls} mt-1`} value={localidade} onChange={(e) => setLocalidade(e.target.value)}>
            {subdivOf(pelotao).map((l) => <option key={l}>{l}</option>)}
          </select></label>
        <label className="text-xs">Efetivo<input className={`${inputCls} mt-1`} value={efetivo} onChange={(e) => setEfetivo(e.target.value.toLocaleUpperCase("pt-BR").replace(/\s{2,}/g, " ").replace(/^\s+/, ""))} /></label>
        <div className="md:col-span-2">
          <MultiCheck label="Tipo de OC (marque uma ou mais)" options={OCORRENCIAS.map(([n]) => n)} selected={tiposSel} onChange={toggleTipos} />
        </div>
        {temMunicao && (
          <label className="text-xs">Quantidade de munições<input type="number" min={1} className={`${inputCls} mt-1`} value={municoes} onChange={(e) => trocarMunicoes(Number(e.target.value))} /></label>
        )}
        {(comum.length > 0 || soEntorpecente) && (
          <label className="text-xs">Qtde<input type="number" min={1} disabled={soEntorpecente} className={`${inputCls} mt-1 disabled:cursor-not-allowed disabled:opacity-60`} value={soEntorpecente ? 1 : qtde} onChange={(e) => trocarQtde(Number(e.target.value))} /></label>
        )}
      </div>
      <div className="rounded-md border bg-background p-3 text-sm">
        <div className="flex justify-between gap-4">
          <span className="font-semibold">Pontos calculados</span>
          <b className="text-primary">{tiposSel.length ? totalPontos : 0}</b>
        </div>
      </div>
      <Button onClick={salvar}>{registro ? "Salvar alterações" : "Adicionar dados"}</Button>
      {msg && <p className="text-sm text-muted-foreground">{msg}</p>}
    </div>
  );
}

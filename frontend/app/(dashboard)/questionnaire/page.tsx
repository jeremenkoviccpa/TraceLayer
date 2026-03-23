"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { AutofillAnswerItem, AutofillContextSummary, AutofillResult, QuestionnaireAnswer, QuestionnaireComment, QuestionnaireResult, QuestionnaireSession, QuestionnaireType } from "@/lib/types";
import {
  Sparkles, Copy, Check, Download, ChevronDown, ChevronUp,
  ClipboardList, Wand2, FileQuestion, Database, Plug, ShieldCheck,
  AlertTriangle, Siren, Bug, Building2, GraduationCap, BookOpen,
  Server, RefreshCw, ShieldX, UserSearch, ClipboardCheck, PenTool,
  UserCheck, Info, Upload, FolderOpen, MessageSquare, Trash2, X,
  Users, CheckCircle2,
} from "lucide-react";
import { PlanGate } from "@/components/plan-gate";
import { showToast } from "@/components/ui/Toaster";

type Tab = "templates" | "custom" | "upload" | "saved";

const TYPE_LABELS: Record<string, { label: string; color: string }> = {
  soc2:     { label: "SOC 2",      color: "#6366F1" },
  iso27001: { label: "ISO 27001",  color: "#0EA5E9" },
  gdpr:     { label: "GDPR",       color: "#10B981" },
  hipaa:    { label: "HIPAA",      color: "#F59E0B" },
  pci:      { label: "PCI DSS",    color: "#EF4444" },
  general:  { label: "General Security", color: "#A855F7" },
};

// ── Context panel ─────────────────────────────────────────────────────────────

function ContextPanel({ ctx }: { ctx: AutofillContextSummary }) {
  const typeInfo = TYPE_LABELS[ctx.detected_type] ?? TYPE_LABELS.general;

  const sources = [
    { icon: Plug,          label: "Integrations",      value: ctx.integrations_count,       active: ctx.integrations_count > 0 },
    { icon: BookOpen,      label: "Policies",           value: ctx.policies_count,           active: ctx.policies_count > 0 },
    { icon: ShieldCheck,   label: "Controls",           value: ctx.risks_count,              active: ctx.risks_count > 0 },
    { icon: AlertTriangle, label: "Risks",              value: ctx.risks_count,              active: ctx.risks_count > 0 },
    { icon: Building2,     label: "Vendors",            value: ctx.vendors_count,            active: ctx.vendors_count > 0 },
    { icon: Server,        label: "Assets",             value: ctx.assets_count,             active: ctx.assets_count > 0 },
    { icon: Siren,         label: "Incidents",          value: ctx.incidents_count,          active: ctx.incidents_count > 0 },
    { icon: Bug,           label: "Vulnerabilities",    value: ctx.vulnerabilities_count,    active: ctx.vulnerabilities_count > 0 },
    { icon: PenTool,       label: "Pen Test",           value: ctx.pen_test ? 1 : 0,         active: ctx.pen_test },
    { icon: GraduationCap, label: "Training",           value: ctx.training_count,           active: ctx.training_count > 0 },
    { icon: UserCheck,     label: "Access Reviews",     value: 0,                            active: false },
    { icon: RefreshCw,     label: "BCP/DR",             value: ctx.bcp_count,                active: ctx.bcp_count > 0 },
    { icon: ClipboardCheck,label: "SoA",                value: ctx.soa_count,                active: ctx.soa_count > 0 },
    { icon: Database,      label: "RoPA",               value: ctx.ropa_count,               active: ctx.ropa_count > 0 },
    { icon: ShieldX,       label: "Breach Register",    value: ctx.breaches_count,           active: true },
    { icon: UserSearch,    label: "Subject Requests",   value: ctx.subject_requests_count,   active: true },
    { icon: ClipboardList, label: "Mgmt Reviews",       value: ctx.management_review ? 1 : 0, active: ctx.management_review },
  ];

  const activeSources = sources.filter((s) => s.active).length;

  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-5">
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-gray-400" />
          <p className="text-sm font-semibold text-gray-800">Data sources used</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs px-2.5 py-1 rounded-full font-semibold text-white" style={{ backgroundColor: typeInfo.color }}>
            {typeInfo.label} detected
          </span>
          <span className="text-xs text-gray-400 font-medium">{activeSources}/{sources.length} sources active</span>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
        {sources.map(({ icon: Icon, label, value, active }) => (
          <div
            key={label}
            className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-xs font-medium transition-colors
              ${active
                ? "border-teal-200 bg-teal-50 text-teal-700"
                : "border-gray-100 bg-gray-50 text-gray-400"
              }`}
          >
            <Icon className={`w-3.5 h-3.5 shrink-0 ${active ? "text-teal-500" : "text-gray-300"}`} />
            <span className="truncate">{label}</span>
            {active && value > 0 && (
              <span className="ml-auto shrink-0 font-bold text-teal-600">{value}</span>
            )}
            {active && value === 0 && (
              <span className="ml-auto shrink-0 w-1.5 h-1.5 rounded-full bg-teal-400" />
            )}
          </div>
        ))}
      </div>

      <p className="text-xs text-gray-400 mt-3">
        AI answers are grounded exclusively in your real compliance data above. The more data you have, the more specific and accurate the answers.
      </p>
    </div>
  );
}

// ── Shared helpers ────────────────────────────────────────────────────────────

function CopyAllButton({ onClick, copied }: { onClick: () => void; copied: boolean }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-1.5 text-xs font-semibold text-gray-600 border border-gray-200 px-3 py-1.5 rounded-lg hover:bg-gray-50 transition-colors"
    >
      {copied ? <><Check className="w-3.5 h-3.5 text-emerald-500" /> Copied</> : <><Copy className="w-3.5 h-3.5" /> Copy all</>}
    </button>
  );
}

// ── Templates tab ─────────────────────────────────────────────────────────────

function TemplatesTab() {
  const [types, setTypes] = useState<QuestionnaireType[]>([]);
  const [selected, setSelected] = useState("");
  const [result, setResult] = useState<QuestionnaireResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [edits, setEdits] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.getQuestionnaireTypes()
      .then((t) => { setTypes(t); if (t.length > 0) setSelected(t[0].id); })
      .catch(() => {});
  }, []);

  const generate = async () => {
    if (!selected) return;
    setLoading(true);
    setResult(null);
    setEdits({});
    try {
      const r = await api.generateQuestionnaire(selected);
      setResult(r);
    } catch { /* ignore */ } finally { setLoading(false); }
  };

  const getAnswer = (qa: QuestionnaireAnswer) => edits[qa.id] ?? qa.answer;

  const copyAll = () => {
    if (!result) return;
    const text = result.answers.map((qa) => `Q: ${qa.question}\nA: ${getAnswer(qa)}`).join("\n\n");
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadCsv = () => {
    if (!result) return;
    const rows = [["Question", "Answer"], ...result.answers.map((qa) => [qa.question, getAnswer(qa)])];
    const csv = rows.map((r) => r.map((c) => `"${c.replace(/"/g, '""')}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${result.questionnaire_type}-questionnaire.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const saveToSaved = async () => {
    if (!result) return;
    setSaving(true);
    try {
      await api.createQuestionnaireSession({
        title: result.name,
        questionnaire_type: result.questionnaire_type,
        answers: (result.answers ?? []).map(qa => ({ question: qa.question, answer: getAnswer(qa) })),
      });
      setSaved(true);
      showToast("Saved to Saved Questionnaires");
    } catch (e: unknown) {
      showToast(e instanceof Error ? e.message : "Failed to save", "error");
    } finally {
      setSaving(false);
    }
  };

  const totalQuestions = result?.answers?.length ?? 0;
  const answeredCount = result ? (result.answers ?? []).filter((qa) => getAnswer(qa).trim().length > 0).length : 0;
  const completionRate = totalQuestions > 0 ? Math.round((answeredCount / totalQuestions) * 100) : 0;

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: "rgba(168,85,247,0.1)" }}>
            <Sparkles className="w-4 h-4" style={{ color: "#A855F7" }} />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-800">Generate from template</p>
            <p className="text-xs text-gray-400">Pre-built frameworks filled with your company name</p>
          </div>
        </div>
        <div className="flex items-end gap-3 flex-wrap">
          <div className="flex-1 min-w-48">
            <label className="block text-xs font-medium text-gray-500 mb-1.5">Questionnaire type</label>
            <select
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
              className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500/30 focus:border-purple-400"
            >
              {types.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </div>
          <button
            onClick={generate}
            disabled={loading || !selected}
            className="flex items-center gap-2 text-white font-semibold px-5 py-2.5 rounded-xl text-sm transition-opacity disabled:opacity-40 shadow-md"
            style={{ backgroundColor: "#A855F7" }}
          >
            {loading ? (
              <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Generating…</>
            ) : (
              <><Sparkles className="w-4 h-4" />Generate answers</>
            )}
          </button>
        </div>
      </div>

      {result && (
        <>
          <div className="bg-white rounded-2xl border border-gray-100 p-5">
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div>
                <p className="text-sm font-semibold text-gray-800">{result.name}</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {result.answers?.length ?? 0} questions · {result.company_name} · Generated {result.generated_at ? new Date(result.generated_at).toLocaleString() : ""}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <div className="hidden sm:block w-32">
                  <div className="flex justify-between text-[10px] font-medium text-gray-400 mb-1">
                    <span>Progress</span><span>{completionRate}%</span>
                  </div>
                  <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full rounded-full transition-all duration-500" style={{ width: `${completionRate}%`, backgroundColor: "#A855F7" }} />
                  </div>
                </div>
                <div className="flex gap-2">
                  <CopyAllButton onClick={copyAll} copied={copied} />
                  <button onClick={downloadCsv} className="flex items-center gap-1.5 text-xs font-semibold text-gray-600 border border-gray-200 px-3 py-1.5 rounded-lg hover:bg-gray-50 transition-colors">
                    <Download className="w-3.5 h-3.5" /> Export CSV
                  </button>
                  <button onClick={saveToSaved} disabled={saving || saved} className="flex items-center gap-1.5 text-xs font-semibold text-indigo-600 border border-indigo-200 hover:bg-indigo-50 px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50">
                    <FolderOpen className="w-3.5 h-3.5" /> {saved ? "Saved ✓" : saving ? "Saving…" : "Save"}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-2">
            {(result.answers ?? []).map((qa, i) => {
              const isOpen = expanded === qa.id;
              const hasEdit = !!edits[qa.id];
              return (
                <div key={qa.id} className={`bg-white rounded-2xl border overflow-hidden transition-all ${isOpen ? "border-purple-200 shadow-sm" : "border-gray-100 hover:border-purple-100"}`}>
                  <button className="w-full flex items-start gap-3.5 px-5 py-4 text-left group" onClick={() => setExpanded(isOpen ? null : qa.id)}>
                    <span className="w-6 h-6 rounded-lg text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5 transition-colors" style={{ backgroundColor: isOpen ? "rgba(168,85,247,0.15)" : "rgba(168,85,247,0.08)", color: "#A855F7" }}>{i + 1}</span>
                    <p className="flex-1 text-sm font-medium text-gray-800 leading-snug">{qa.question}</p>
                    {hasEdit && !isOpen && <span className="text-[10px] font-semibold text-purple-500 bg-purple-50 px-2 py-0.5 rounded-full shrink-0">Edited</span>}
                    {isOpen ? <ChevronUp className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" /> : <ChevronDown className="w-4 h-4 text-gray-300 shrink-0 mt-0.5 group-hover:text-purple-300 transition-colors" />}
                  </button>
                  {isOpen && (
                    <div className="border-t border-purple-100 px-5 py-4 bg-purple-50/30">
                      <label className="block text-[10px] font-semibold uppercase tracking-wide mb-2" style={{ color: "#A855F7" }}>Answer — click to edit</label>
                      <textarea
                        value={getAnswer(qa)}
                        onChange={(e) => setEdits((prev) => ({ ...prev, [qa.id]: e.target.value }))}
                        rows={3}
                        className="w-full text-sm text-gray-700 leading-relaxed bg-white border border-purple-200 rounded-xl px-3.5 py-2.5 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500/30 focus:border-purple-400 transition-colors"
                      />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

// ── Custom Questions tab ──────────────────────────────────────────────────────

function CustomQuestionsTab() {
  const [input, setInput] = useState("");
  const [result, setResult] = useState<AutofillResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [edits, setEdits] = useState<Record<number, string>>({});
  const [savingSession, setSavingSession] = useState(false);
  const [savedSession, setSavedSession] = useState(false);;

  const questions = input.split("\n").map((l) => l.trim()).filter(Boolean);

  const autofill = async () => {
    if (questions.length === 0) return;
    setLoading(true);
    setResult(null);
    setEdits({});
    setError("");
    try {
      const r = await api.aiAutofillQuestionnaire(questions);
      setResult(r);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Something went wrong";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const getAnswer = (item: AutofillAnswerItem, i: number) => edits[i] ?? item.answer;

  const copyAll = () => {
    if (!result) return;
    const text = result.answers.map((a, i) => `Q: ${a.question}\nA: ${getAnswer(a, i)}`).join("\n\n");
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadCsv = () => {
    if (!result) return;
    const rows = [["Question", "Answer"], ...result.answers.map((a, i) => [a.question, getAnswer(a, i)])];
    const csv = rows.map((r) => r.map((c) => `"${c.replace(/"/g, '""')}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "custom-questionnaire.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  const saveToSaved = async () => {
    if (!result) return;
    setSavingSession(true);
    try {
      await api.createQuestionnaireSession({
        title: `Custom Questionnaire — ${new Date().toLocaleDateString()}`,
        questionnaire_type: result.detected_type,
        answers: result.answers.map((a, i) => ({ question: a.question, answer: edits[i] ?? a.answer })),
      });
      setSavedSession(true);
      showToast("Saved to Saved Questionnaires");
    } catch (e: unknown) {
      showToast(e instanceof Error ? e.message : "Failed to save", "error");
    } finally {
      setSavingSession(false);
    }
  };

  const typeInfo = result ? (TYPE_LABELS[result.detected_type] ?? TYPE_LABELS.general) : null;

  return (
    <div className="space-y-4">
      {/* Input Card */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: "rgba(20,184,166,0.1)" }}>
            <Wand2 className="w-4 h-4" style={{ color: "#14B8A6" }} />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-800">AI autofill from your compliance data</p>
            <p className="text-xs text-gray-400">Paste any vendor questionnaire — AI drafts answers grounded in your actual data across 17 compliance data sources</p>
          </div>
        </div>

        <label className="block text-xs font-medium text-gray-500 mb-1.5">
          Paste questions — one per line
        </label>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={"Do you have an information security policy?\nDo you enforce MFA for all employees?\nHow do you manage vendor risk?\nDo you maintain a record of processing activities?"}
          rows={8}
          className="w-full border border-gray-200 rounded-xl px-3.5 py-3 text-sm text-gray-700 leading-relaxed resize-none focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-400 transition-colors placeholder:text-gray-300"
        />

        <div className="flex items-center justify-between mt-3 flex-wrap gap-2">
          <p className="text-xs text-gray-400">
            {questions.length > 0
              ? `${questions.length} question${questions.length !== 1 ? "s" : ""} · max 100`
              : "Enter at least one question — up to 100"}
          </p>
          <button
            onClick={autofill}
            disabled={loading || questions.length === 0}
            className="flex items-center gap-2 text-white font-semibold px-5 py-2.5 rounded-xl text-sm transition-opacity disabled:opacity-40 shadow-md"
            style={{ backgroundColor: "#14B8A6" }}
          >
            {loading ? (
              <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Drafting answers…</>
            ) : (
              <><Wand2 className="w-4 h-4" />Autofill with AI</>
            )}
          </button>
        </div>

        {error && (
          <p className="mt-3 text-xs text-red-500 bg-red-50 rounded-lg px-3 py-2">{error}</p>
        )}
      </div>

      {result && (
        <>
          {/* Context panel */}
          <ContextPanel ctx={result.context} />

          {/* Results header */}
          <div className="bg-white rounded-2xl border border-gray-100 p-5">
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div>
                <div className="flex items-center gap-2 mb-0.5">
                  <p className="text-sm font-semibold text-gray-800">AI-drafted answers</p>
                  {typeInfo && (
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full text-white" style={{ backgroundColor: typeInfo.color }}>
                      {typeInfo.label}
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-400">
                  {result.answers?.length ?? 0} questions · {result.company_name} · {result.generated_at ? new Date(result.generated_at).toLocaleString() : ""}
                </p>
              </div>
              <div className="flex gap-2">
                <CopyAllButton onClick={copyAll} copied={copied} />
                <button onClick={downloadCsv} className="flex items-center gap-1.5 text-xs font-semibold text-gray-600 border border-gray-200 px-3 py-1.5 rounded-lg hover:bg-gray-50 transition-colors">
                  <Download className="w-3.5 h-3.5" /> Export CSV
                </button>
                <button onClick={saveToSaved} disabled={savingSession || savedSession} className="flex items-center gap-1.5 text-xs font-semibold text-indigo-600 border border-indigo-200 hover:bg-indigo-50 px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50">
                  <FolderOpen className="w-3.5 h-3.5" /> {savedSession ? "Saved ✓" : savingSession ? "Saving…" : "Save"}
                </button>
              </div>
            </div>
          </div>

          {/* Answer cards */}
          <div className="space-y-2">
            {(result.answers ?? []).map((item, i) => {
              const isOpen = expanded === i;
              const hasEdit = edits[i] !== undefined;
              return (
                <div key={i} className={`bg-white rounded-2xl border overflow-hidden transition-all ${isOpen ? "border-teal-200 shadow-sm" : "border-gray-100 hover:border-teal-100"}`}>
                  <button className="w-full flex items-start gap-3.5 px-5 py-4 text-left group" onClick={() => setExpanded(isOpen ? null : i)}>
                    <span className="w-6 h-6 rounded-lg text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5" style={{ backgroundColor: isOpen ? "rgba(20,184,166,0.15)" : "rgba(20,184,166,0.08)", color: "#14B8A6" }}>{i + 1}</span>
                    <p className="flex-1 text-sm font-medium text-gray-800 leading-snug">{item.question}</p>
                    {hasEdit && !isOpen && <span className="text-[10px] font-semibold text-teal-600 bg-teal-50 px-2 py-0.5 rounded-full shrink-0">Edited</span>}
                    {isOpen ? <ChevronUp className="w-4 h-4 text-teal-400 shrink-0 mt-0.5" /> : <ChevronDown className="w-4 h-4 text-gray-300 shrink-0 mt-0.5 group-hover:text-teal-300 transition-colors" />}
                  </button>
                  {isOpen && (
                    <div className="border-t border-teal-100 px-5 py-4 bg-teal-50/20">
                      <div className="flex items-center gap-2 mb-2">
                        <label className="block text-[10px] font-semibold uppercase tracking-wide" style={{ color: "#14B8A6" }}>AI-drafted answer — click to edit</label>
                        <span className="text-[10px] bg-teal-100 text-teal-700 px-1.5 py-0.5 rounded-full font-medium">AI</span>
                      </div>
                      <textarea
                        value={getAnswer(item, i)}
                        onChange={(e) => setEdits((prev) => ({ ...prev, [i]: e.target.value }))}
                        rows={4}
                        className="w-full text-sm text-gray-700 leading-relaxed bg-white border border-teal-200 rounded-xl px-3.5 py-2.5 resize-none focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-400 transition-colors"
                      />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

// ── Upload tab ────────────────────────────────────────────────────────────────

function UploadTab() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [done, setDone] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFile = (f: File | null) => {
    if (!f) return;
    const ok = f.name.endsWith(".csv") || f.name.endsWith(".xlsx") || f.name.endsWith(".xls");
    if (!ok) { showToast("Only .csv and .xlsx files supported", "error"); return; }
    setFile(f);
    setDone(false);
  };

  const upload = async () => {
    if (!file) return;
    setUploading(true);
    setDone(false);
    try {
      await api.uploadQuestionnaire(file);
      setDone(true);
      showToast("Answered questionnaire downloaded!");
    } catch (e: unknown) {
      showToast(e instanceof Error ? e.message : "Upload failed", "error");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 rounded-lg bg-orange-100 flex items-center justify-center">
            <Upload className="w-4 h-4 text-orange-500" />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-800">Upload & AI-answer your questionnaire file</p>
            <p className="text-xs text-gray-400">Upload a CSV or Excel file — questions in column A — AI fills in answers and returns the completed file</p>
          </div>
        </div>

        {/* Drop zone */}
        <div
          onClick={() => fileRef.current?.click()}
          onDragOver={e => { e.preventDefault(); }}
          onDrop={e => { e.preventDefault(); handleFile(e.dataTransfer.files[0] ?? null); }}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all
            ${file ? "border-orange-200 bg-orange-50" : "border-gray-200 bg-gray-50 hover:border-orange-300 hover:bg-orange-50/30"}`}
        >
          <input
            ref={fileRef}
            type="file"
            accept=".csv,.xlsx,.xls"
            className="hidden"
            onChange={e => handleFile(e.target.files?.[0] ?? null)}
          />
          {file ? (
            <div className="flex items-center justify-center gap-3">
              <FileQuestion className="w-6 h-6 text-orange-400" />
              <div className="text-left">
                <p className="font-semibold text-gray-800 text-sm">{file.name}</p>
                <p className="text-xs text-gray-400">{(file.size / 1024).toFixed(1)} KB</p>
              </div>
              <button
                onClick={e => { e.stopPropagation(); setFile(null); setDone(false); }}
                className="ml-2 text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <>
              <Upload className="w-8 h-8 text-gray-300 mx-auto mb-2" />
              <p className="text-sm font-medium text-gray-500">Click or drag a file here</p>
              <p className="text-xs text-gray-400 mt-1">.csv, .xlsx — questions in column A</p>
            </>
          )}
        </div>

        {/* Expected format */}
        <div className="mt-4 bg-gray-50 rounded-xl p-3">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-gray-400 mb-2">Expected file format</p>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-gray-400 border-b border-gray-200">
                  <th className="text-left pb-1 font-medium">Column A (required)</th>
                  <th className="text-left pb-1 font-medium">Column B (optional, will be filled)</th>
                </tr>
              </thead>
              <tbody className="text-gray-500">
                <tr><td className="py-0.5 pr-4">Do you encrypt data at rest?</td><td className="py-0.5 text-gray-300">(blank — AI fills this)</td></tr>
                <tr><td className="py-0.5 pr-4">Do you have an incident response plan?</td><td className="py-0.5 text-gray-300">(blank — AI fills this)</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <div className="flex items-center justify-between mt-4">
          {done ? (
            <div className="flex items-center gap-2 text-sm text-emerald-600 font-semibold">
              <CheckCircle2 className="w-4 h-4" />
              Answered file downloaded!
            </div>
          ) : <div />}
          <button
            onClick={upload}
            disabled={!file || uploading}
            className="flex items-center gap-2 bg-orange-500 hover:bg-orange-600 text-white font-semibold px-5 py-2.5 rounded-xl text-sm transition-colors disabled:opacity-40 shadow-md"
          >
            {uploading ? (
              <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Processing…</>
            ) : (
              <><Sparkles className="w-4 h-4" />AI-fill & download</>
            )}
          </button>
        </div>
      </div>

      <div className="bg-amber-50 border border-amber-100 rounded-xl px-4 py-3 flex items-start gap-2.5">
        <Info className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
        <p className="text-xs text-amber-700">
          AI answers are drafted from your compliance data and should be reviewed before sending to vendors. This feature requires a Growth plan.
        </p>
      </div>
    </div>
  );
}


// ── Saved Sessions tab ────────────────────────────────────────────────────────

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-600",
  in_review: "bg-amber-100 text-amber-700",
  completed: "bg-emerald-100 text-emerald-700",
};

function CommentsPanel({ sessionId, questionIndex, onClose }: {
  sessionId: string;
  questionIndex: number;
  onClose: () => void;
}) {
  const [comments, setComments] = useState<QuestionnaireComment[]>([]);
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const fetchComments = async () => {
    try {
      const all = await api.getSessionComments(sessionId);
      setComments(all.filter(c => c.question_index === questionIndex));
    } catch {
      // silent
    }
  };

  useEffect(() => {
    fetchComments();
  }, [sessionId, questionIndex]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [comments]);

  const send = async () => {
    if (!text.trim()) return;
    setSending(true);
    try {
      await api.addSessionComment(sessionId, questionIndex, text);
      setText("");
      await fetchComments();
    } catch (e: unknown) {
      showToast(e instanceof Error ? e.message : "Failed to add comment", "error");
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="bg-slate-900 rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Comments — Q{questionIndex + 1}</p>
        <button onClick={onClose} className="text-slate-500 hover:text-slate-300 p-0.5 rounded transition-colors">
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
      <div ref={scrollRef} className="space-y-2 max-h-40 overflow-y-auto">
        {comments.length === 0 ? (
          <p className="text-xs text-slate-500 text-center py-3">No comments yet</p>
        ) : comments.map(c => (
          <div key={c.id} className="bg-slate-800 rounded-lg px-3 py-2">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[10px] font-semibold text-slate-400">{c.user_email || "Unknown"}</span>
              <span className="text-[10px] text-slate-600">{new Date(c.created_at).toLocaleString()}</span>
            </div>
            <p className="text-xs text-slate-300">{c.comment_text}</p>
          </div>
        ))}
      </div>
      <div className="flex items-center gap-2">
        <input
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={e => e.key === "Enter" && !e.shiftKey && send()}
          placeholder="Add a comment…"
          className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none focus:ring-1 focus:ring-teal-500"
        />
        <button
          onClick={send}
          disabled={sending || !text.trim()}
          className="bg-teal-600 hover:bg-teal-500 text-white px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors disabled:opacity-40"
        >
          {sending ? "…" : "Send"}
        </button>
      </div>
    </div>
  );
}

function SavedTab() {
  const [sessions, setSessions] = useState<QuestionnaireSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [openComments, setOpenComments] = useState<{ sessionId: string; qIdx: number } | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [updatingStatus, setUpdatingStatus] = useState<string | null>(null);

  useEffect(() => {
    api.getQuestionnaireSessions()
      .then(setSessions)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const deleteSession = async (id: string) => {
    setDeleting(id);
    try {
      await api.deleteQuestionnaireSession(id);
      setSessions(prev => prev.filter(s => s.id !== id));
      showToast("Session deleted");
    } catch (e: unknown) {
      showToast(e instanceof Error ? e.message : "Failed to delete", "error");
    } finally {
      setDeleting(null);
    }
  };

  const cycleStatus = async (session: QuestionnaireSession) => {
    const cycle: QuestionnaireSession["status"][] = ["draft", "in_review", "completed"];
    const next = cycle[(cycle.indexOf(session.status) + 1) % cycle.length];
    setUpdatingStatus(session.id);
    try {
      const updated = await api.updateQuestionnaireSession(session.id, { status: next });
      setSessions(prev => prev.map(s => s.id === session.id ? updated : s));
    } catch {
      showToast("Failed to update status", "error");
    } finally {
      setUpdatingStatus(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="w-6 h-6 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (sessions.length === 0) {
    return (
      <div className="text-center py-16 bg-white rounded-2xl border border-gray-100">
        <FolderOpen className="w-12 h-12 text-gray-200 mx-auto mb-3" />
        <p className="font-semibold text-gray-400">No saved questionnaires</p>
        <p className="text-sm text-gray-300 mt-1">Generate answers from the Templates or AI Autofill tabs, then save them here to collaborate with your team.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {sessions.map(session => {
        const isOpen = expanded === session.id;
        return (
          <div key={session.id} className={`bg-white rounded-2xl border overflow-hidden transition-all ${isOpen ? "border-teal-200 shadow-sm" : "border-gray-100 hover:border-gray-200"}`}>
            <div className="flex items-center gap-4 px-5 py-4">
              <button
                className="flex-1 flex items-center gap-3 text-left min-w-0"
                onClick={() => setExpanded(isOpen ? null : session.id)}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-0.5">
                    <p className="font-semibold text-gray-800 text-sm truncate">{session.title}</p>
                    <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${STATUS_COLORS[session.status]}`}>
                      {session.status.replace("_", " ")}
                    </span>
                    {session.questionnaire_type && (
                      <span className="text-[10px] font-medium text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
                        {session.questionnaire_type.toUpperCase()}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 text-xs text-gray-400">
                    <span>{session.answers.length} questions</span>
                    {session.assigned_to_email && (
                      <span className="flex items-center gap-1"><Users className="w-3 h-3" />{session.assigned_to_email}</span>
                    )}
                    {session.comment_count > 0 && (
                      <span className="flex items-center gap-1"><MessageSquare className="w-3 h-3" />{session.comment_count} comments</span>
                    )}
                    <span>{new Date(session.updated_at).toLocaleDateString()}</span>
                  </div>
                </div>
                {isOpen ? <ChevronUp className="w-4 h-4 text-teal-400 shrink-0" /> : <ChevronDown className="w-4 h-4 text-gray-300 shrink-0" />}
              </button>
              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => cycleStatus(session)}
                  disabled={updatingStatus === session.id}
                  title="Click to advance status"
                  className="text-xs font-medium text-gray-500 hover:text-teal-600 border border-gray-200 hover:border-teal-300 px-2 py-1 rounded-lg transition-colors disabled:opacity-40"
                >
                  {updatingStatus === session.id ? "…" : "▶ Next status"}
                </button>
                <button
                  onClick={() => deleteSession(session.id)}
                  disabled={deleting === session.id}
                  className="text-red-400 hover:text-red-600 hover:bg-red-50 p-1.5 rounded-lg transition-colors disabled:opacity-40"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {isOpen && (
              <div className="border-t border-teal-100 px-5 py-4 bg-teal-50/20 space-y-2">
                {session.answers.map((qa, i) => {
                  const isCommenting = openComments?.sessionId === session.id && openComments.qIdx === i;
                  return (
                    <div key={i} className="bg-white rounded-xl border border-gray-100 overflow-hidden">
                      <div className="flex items-start gap-3 px-4 py-3">
                        <span className="w-6 h-6 rounded-lg bg-teal-100 text-teal-600 text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5">
                          {i + 1}
                        </span>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-700 leading-snug mb-1.5">{qa.question}</p>
                          <p className="text-xs text-gray-500 leading-relaxed line-clamp-2">{qa.answer}</p>
                        </div>
                        <button
                          onClick={() => setOpenComments(isCommenting ? null : { sessionId: session.id, qIdx: i })}
                          className={`flex items-center gap-1 text-xs px-2 py-1 rounded-lg transition-colors shrink-0 ${isCommenting ? "bg-slate-900 text-white" : "text-gray-400 hover:text-gray-600 hover:bg-gray-100"}`}
                        >
                          <MessageSquare className="w-3 h-3" />
                          Comment
                        </button>
                      </div>
                      {isCommenting && (
                        <div className="border-t border-gray-100 px-4 pb-3">
                          <CommentsPanel
                            sessionId={session.id}
                            questionIndex={i}
                            onClose={() => setOpenComments(null)}
                          />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}


// ── Page ──────────────────────────────────────────────────────────────────────

export default function QuestionnairePage() {
  const [tab, setTab] = useState<Tab>("custom");

  return (
    <div className="space-y-6 overflow-x-hidden">
      {/* Hero */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl p-6 shadow-xl">
        <div className="flex items-start gap-4">
          <div className="w-11 h-11 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "rgba(168,85,247,0.2)" }}>
            <ClipboardList className="w-5 h-5" style={{ color: "#A855F7" }} />
          </div>
          <div className="flex-1">
            <h1 className="text-xl font-bold text-white">Security Questionnaire</h1>
            <p className="text-sm text-slate-400 mt-0.5">Answer vendor security questionnaires in minutes — AI drafts answers grounded in your real compliance data.</p>
            <div className="flex flex-wrap gap-3 sm:gap-6 mt-4">
              <div>
                <p className="text-2xl font-bold" style={{ color: "#14B8A6" }}>17</p>
                <p className="text-xs text-slate-500 mt-0.5">Data sources</p>
              </div>
              <div className="hidden sm:block w-px h-8 bg-slate-700 self-center" />
              <div>
                <p className="text-2xl font-bold" style={{ color: "#A855F7" }}>3</p>
                <p className="text-xs text-slate-500 mt-0.5">Questionnaire templates</p>
              </div>
              <div className="hidden sm:block w-px h-8 bg-slate-700 self-center" />
              <div>
                <p className="text-2xl font-bold text-slate-300">100</p>
                <p className="text-xs text-slate-500 mt-0.5">Questions / run</p>
              </div>
              <div className="hidden sm:block w-px h-8 bg-slate-700 self-center" />
              <div>
                <p className="text-2xl font-bold text-slate-300">SOC 2 · ISO · GDPR · HIPAA · PCI</p>
                <p className="text-xs text-slate-500 mt-0.5">Auto-detected frameworks</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 rounded-xl p-1 flex-wrap w-fit">
        <button
          onClick={() => setTab("custom")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${tab === "custom" ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"}`}
        >
          <Wand2 className="w-4 h-4" style={{ color: tab === "custom" ? "#14B8A6" : undefined }} />
          AI Autofill
        </button>
        <button
          onClick={() => setTab("templates")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${tab === "templates" ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"}`}
        >
          <FileQuestion className="w-4 h-4" style={{ color: tab === "templates" ? "#A855F7" : undefined }} />
          Templates
        </button>
        <button
          onClick={() => setTab("upload")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${tab === "upload" ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"}`}
        >
          <Upload className="w-4 h-4" style={{ color: tab === "upload" ? "#F97316" : undefined }} />
          Upload File
        </button>
        <button
          onClick={() => setTab("saved")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${tab === "saved" ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"}`}
        >
          <FolderOpen className="w-4 h-4" style={{ color: tab === "saved" ? "#6366F1" : undefined }} />
          Saved
        </button>
      </div>

      {tab === "custom" ? (
        <PlanGate feature="AI Questionnaire Autofill" mode="blur">
          <CustomQuestionsTab />
        </PlanGate>
      ) : tab === "templates" ? (
        <TemplatesTab />
      ) : tab === "upload" ? (
        <PlanGate feature="Upload & AI-Answer Questionnaire Files" mode="blur">
          <UploadTab />
        </PlanGate>
      ) : (
        <SavedTab />
      )}
    </div>
  );
}

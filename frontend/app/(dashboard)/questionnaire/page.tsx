"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { QuestionnaireAnswer, QuestionnaireResult, QuestionnaireType } from "@/lib/types";
import { Sparkles, Copy, Check, Download, ChevronDown, ChevronUp, ClipboardList, BarChart3 } from "lucide-react";

export default function QuestionnairePage() {
  const [types, setTypes]       = useState<QuestionnaireType[]>([]);
  const [selected, setSelected] = useState("");
  const [result, setResult]     = useState<QuestionnaireResult | null>(null);
  const [loading, setLoading]   = useState(false);
  const [copied, setCopied]     = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [edits, setEdits]       = useState<Record<string, string>>({});

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
    const text = result.answers
      .map((qa) => `Q: ${qa.question}\nA: ${getAnswer(qa)}`)
      .join("\n\n");
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

  // Compute stats
  const totalQuestions = result?.answers.length ?? 0;
  const answeredCount = result
    ? result.answers.filter((qa) => {
        const ans = getAnswer(qa);
        return ans && ans.trim().length > 0;
      }).length
    : 0;
  const completionRate = totalQuestions > 0 ? Math.round((answeredCount / totalQuestions) * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Dark Hero Card */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl p-6 shadow-xl">
        <div className="flex items-start gap-4">
          {/* Icon */}
          <div className="w-11 h-11 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "rgba(168,85,247,0.2)" }}>
            <ClipboardList className="w-5 h-5" style={{ color: "#A855F7" }} />
          </div>
          {/* Title + stats */}
          <div className="flex-1">
            <h1 className="text-xl font-bold text-white">Security Questionnaire</h1>
            <p className="text-sm text-slate-400 mt-0.5">Answer security questionnaires faster with AI-assisted responses.</p>
            <div className="flex items-center gap-6 mt-4">
              <div>
                <p className="text-2xl font-bold" style={{ color: "#A855F7" }}>
                  {result ? answeredCount : "—"}
                </p>
                <p className="text-xs text-slate-500 mt-0.5">Questions answered</p>
              </div>
              <div className="w-px h-8 bg-slate-700" />
              <div>
                <p className="text-2xl font-bold" style={{ color: "#A855F7" }}>
                  {result ? `${completionRate}%` : "—"}
                </p>
                <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-1">
                  <BarChart3 className="w-3 h-3" /> Completion rate
                </p>
              </div>
              {result && (
                <>
                  <div className="w-px h-8 bg-slate-700" />
                  <div>
                    <p className="text-2xl font-bold text-slate-300">{totalQuestions}</p>
                    <p className="text-xs text-slate-500 mt-0.5">Total questions</p>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Generator Card */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: "rgba(168,85,247,0.1)" }}>
            <Sparkles className="w-4 h-4" style={{ color: "#A855F7" }} />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-800">Generate answers</p>
            <p className="text-xs text-gray-400">AI-assisted from your compliance data</p>
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
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Generating…
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Generate answers
              </>
            )}
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-3">
          Answers are pre-filled based on your company name and standard compliance controls. Review and edit each answer before sending.
        </p>
      </div>

      {result && (
        <>
          {/* Result Header */}
          <div className="bg-white rounded-2xl border border-gray-100 p-5">
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div>
                <p className="text-sm font-semibold text-gray-800">{result.name}</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {result.answers.length} questions &middot; {result.company_name} &middot; Generated {new Date(result.generated_at).toLocaleString()}
                </p>
              </div>

              {/* Completion bar */}
              <div className="flex items-center gap-3">
                <div className="hidden sm:block w-32">
                  <div className="flex justify-between text-[10px] font-medium text-gray-400 mb-1">
                    <span>Progress</span>
                    <span>{completionRate}%</span>
                  </div>
                  <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{ width: `${completionRate}%`, backgroundColor: "#A855F7" }}
                    />
                  </div>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={copyAll}
                    className="flex items-center gap-1.5 text-xs font-semibold text-gray-600 border border-gray-200 px-3 py-1.5 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    {copied
                      ? <><Check className="w-3.5 h-3.5 text-emerald-500" /> Copied</>
                      : <><Copy className="w-3.5 h-3.5" /> Copy all</>
                    }
                  </button>
                  <button
                    onClick={downloadCsv}
                    className="flex items-center gap-1.5 text-xs font-semibold text-gray-600 border border-gray-200 px-3 py-1.5 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <Download className="w-3.5 h-3.5" /> Export CSV
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Q&A List */}
          <div className="space-y-2">
            {result.answers.map((qa, i) => {
              const isOpen = expanded === qa.id;
              const hasEdit = !!edits[qa.id];
              return (
                <div
                  key={qa.id}
                  className={`bg-white rounded-2xl border overflow-hidden transition-all ${isOpen ? "border-purple-200 shadow-sm" : "border-gray-100 hover:border-purple-100"}`}
                >
                  <button
                    className="w-full flex items-start gap-3.5 px-5 py-4 text-left group"
                    onClick={() => setExpanded(isOpen ? null : qa.id)}
                  >
                    {/* Question number */}
                    <span
                      className="w-6 h-6 rounded-lg text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5 transition-colors"
                      style={{
                        backgroundColor: isOpen ? "rgba(168,85,247,0.15)" : "rgba(168,85,247,0.08)",
                        color: "#A855F7",
                      }}
                    >
                      {i + 1}
                    </span>
                    {/* Question text */}
                    <p className="flex-1 text-sm font-medium text-gray-800 leading-snug">{qa.question}</p>
                    {/* Edit indicator */}
                    {hasEdit && !isOpen && (
                      <span className="text-[10px] font-semibold text-purple-500 bg-purple-50 px-2 py-0.5 rounded-full shrink-0">Edited</span>
                    )}
                    {/* Chevron */}
                    {isOpen
                      ? <ChevronUp className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
                      : <ChevronDown className="w-4 h-4 text-gray-300 shrink-0 mt-0.5 group-hover:text-purple-300 transition-colors" />
                    }
                  </button>

                  {isOpen && (
                    <div className="border-t border-purple-100 px-5 py-4 bg-purple-50/30">
                      <label className="block text-[10px] font-semibold uppercase tracking-wide mb-2" style={{ color: "#A855F7" }}>
                        Answer — click to edit
                      </label>
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

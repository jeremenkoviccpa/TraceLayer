"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { QuestionnaireAnswer, QuestionnaireResult, QuestionnaireType } from "@/lib/types";
import { Sparkles, Copy, Check, Download, ChevronDown, ChevronUp } from "lucide-react";

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

  return (
    <div className="animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Questionnaire Auto-fill</h1>
        <p className="text-sm text-gray-500 mt-0.5">Generate pre-filled answers to security questionnaires from your compliance data.</p>
      </div>

      {/* Generator */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-5 mb-6">
        <div className="flex items-end gap-3 flex-wrap">
          <div className="flex-1 min-w-48">
            <label className="block text-xs font-medium text-gray-600 mb-1.5">Questionnaire type</label>
            <select
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
              className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-400"
            >
              {types.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </div>
          <button
            onClick={generate}
            disabled={loading || !selected}
            className="flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white font-semibold px-4 py-2 rounded-xl text-sm transition-colors disabled:opacity-40"
          >
            {loading ? (
              <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Generating…</>
            ) : (
              <><Sparkles className="w-4 h-4 text-violet-300" /> Generate answers</>
            )}
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-3">
          Answers are pre-filled based on your company name and standard compliance controls. Review and edit each answer before sending.
        </p>
      </div>

      {result && (
        <>
          {/* Header */}
          <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
            <div>
              <p className="text-sm font-semibold text-gray-800">{result.name}</p>
              <p className="text-xs text-gray-400">{result.answers.length} questions · {result.company_name} · Generated {new Date(result.generated_at).toLocaleString()}</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={copyAll}
                className="flex items-center gap-1.5 text-xs font-semibold text-gray-600 border border-gray-200 px-3 py-1.5 rounded-lg hover:bg-gray-50 transition-colors"
              >
                {copied ? <><Check className="w-3.5 h-3.5 text-emerald-500" /> Copied</> : <><Copy className="w-3.5 h-3.5" /> Copy all</>}
              </button>
              <button
                onClick={downloadCsv}
                className="flex items-center gap-1.5 text-xs font-semibold text-gray-600 border border-gray-200 px-3 py-1.5 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <Download className="w-3.5 h-3.5" /> Export CSV
              </button>
            </div>
          </div>

          {/* Q&A list */}
          <div className="space-y-2">
            {result.answers.map((qa, i) => (
              <div key={qa.id} className="bg-white rounded-2xl border border-gray-100 shadow-card overflow-hidden">
                <button
                  className="w-full flex items-start gap-3 px-5 py-4 text-left"
                  onClick={() => setExpanded(expanded === qa.id ? null : qa.id)}
                >
                  <span className="w-5 h-5 rounded-full bg-brand-50 text-brand-700 text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5">{i + 1}</span>
                  <p className="flex-1 text-sm font-medium text-gray-800 leading-snug">{qa.question}</p>
                  {expanded === qa.id
                    ? <ChevronUp className="w-4 h-4 text-gray-300 shrink-0 mt-0.5" />
                    : <ChevronDown className="w-4 h-4 text-gray-300 shrink-0 mt-0.5" />
                  }
                </button>
                {expanded === qa.id && (
                  <div className="border-t border-gray-100 px-5 py-3 bg-gray-50/50">
                    <label className="block text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-1.5">Answer — click to edit</label>
                    <textarea
                      value={getAnswer(qa)}
                      onChange={(e) => setEdits((prev) => ({ ...prev, [qa.id]: e.target.value }))}
                      rows={3}
                      className="w-full text-sm text-gray-700 leading-relaxed bg-white border border-gray-200 rounded-xl px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-brand-500/30"
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

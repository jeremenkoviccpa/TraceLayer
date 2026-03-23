"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRight, CheckCircle2, RotateCcw, Zap } from "lucide-react";
import { ToolEmailGate } from "@/components/tool-email-gate";

// ── Quiz data ─────────────────────────────────────────────────────────────────

const QUESTIONS = [
  {
    id: "size",
    question: "How big is your company?",
    type: "single" as const,
    options: [
      { label: "1–10 people", value: "tiny" },
      { label: "11–50 people", value: "small" },
      { label: "51–200 people", value: "medium" },
      { label: "200+ people", value: "large" },
    ],
  },
  {
    id: "tools",
    question: "Which tools does your team use? (select all that apply)",
    type: "multi" as const,
    options: [
      { label: "AWS", value: "aws" },
      { label: "GitHub", value: "github" },
      { label: "Slack", value: "slack" },
      { label: "Google Workspace", value: "google" },
      { label: "Okta", value: "okta" },
      { label: "Azure AD", value: "azure" },
      { label: "Jira", value: "jira" },
    ],
  },
  {
    id: "framework",
    question: "Which compliance framework are you targeting?",
    type: "single" as const,
    options: [
      { label: "SOC 2", value: "soc2" },
      { label: "ISO 27001", value: "iso27001" },
      { label: "HIPAA", value: "hipaa" },
      { label: "Multiple frameworks", value: "multiple" },
      { label: "Not sure yet", value: "unsure" },
    ],
  },
  {
    id: "evidence",
    question: "How do you collect compliance evidence today?",
    type: "single" as const,
    options: [
      { label: "No process yet", value: "none" },
      { label: "Manually in spreadsheets", value: "manual" },
      { label: "Mix of scripts + manual work", value: "mixed" },
      { label: "Using a dedicated tool", value: "tool" },
    ],
  },
  {
    id: "timeline",
    question: "When is your next audit or certification target?",
    type: "single" as const,
    options: [
      { label: "Within 3 months", value: "urgent" },
      { label: "3–6 months", value: "soon" },
      { label: "6–12 months", value: "planned" },
      { label: "No date set yet", value: "none" },
    ],
  },
];

// ── Scoring ───────────────────────────────────────────────────────────────────

type Answers = Record<string, string | string[]>;

function computeResult(answers: Answers) {
  const tools = (answers.tools as string[]) ?? [];
  const automatable = tools.length;
  const automationPct = Math.min(100, Math.round((automatable / 7) * 100));

  const effortMap: Record<string, number> = {
    none: 20,
    manual: 12,
    mixed: 6,
    tool: 1,
  };
  const hoursPerWeek = effortMap[answers.evidence as string] ?? 10;

  const urgencyMap: Record<string, string> = {
    urgent: "high",
    soon: "high",
    planned: "medium",
    none: "low",
  };
  const urgency = urgencyMap[answers.timeline as string] ?? "medium";

  const frameworkLabel: Record<string, string> = {
    soc2: "SOC 2",
    iso27001: "ISO 27001",
    hipaa: "HIPAA",
    multiple: "multiple frameworks",
    unsure: "your target framework",
  };
  const framework = frameworkLabel[answers.framework as string] ?? "your framework";

  // Score = automation coverage
  const score = Math.max(10, automationPct);

  const insights: { type: "good" | "warn" | "info"; text: string }[] = [];

  if (automatable >= 4) {
    insights.push({
      type: "good",
      text: `${automatable} of your tools (${tools.join(", ")}) have direct TraceLayer integrations — evidence collection is fully automated for these.`,
    });
  } else if (automatable > 0) {
    insights.push({
      type: "good",
      text: `${automatable} of your tools can be auto-collected today. TraceLayer maps evidence to ${framework} controls instantly.`,
    });
  } else {
    insights.push({
      type: "warn",
      text: "None of your current tools were selected, but TraceLayer covers AWS, GitHub, Slack, Google Workspace, Okta, Azure AD, and Jira.",
    });
  }

  if (answers.evidence === "none" || answers.evidence === "manual") {
    insights.push({
      type: "warn",
      text: `Manual evidence collection typically takes ${hoursPerWeek}+ hours/week. TraceLayer runs automatically every 24 hours with no ongoing effort.`,
    });
  } else if (answers.evidence === "mixed") {
    insights.push({
      type: "info",
      text: "You're already ahead of most teams. TraceLayer replaces scripts with a unified dashboard, structured evidence, and audit-ready PDF reports.",
    });
  }

  if (urgency === "high") {
    insights.push({
      type: "warn",
      text: "Your audit timeline is tight. Most teams are audit-ready within 2 weeks of connecting their first TraceLayer integration.",
    });
  } else {
    insights.push({
      type: "info",
      text: `Starting early for ${framework} means TraceLayer builds up your evidence history before auditors arrive — giving you a stronger Type II story.`,
    });
  }

  let headline = "";
  let subline = "";
  if (score >= 70) {
    headline = "Strong automation potential";
    subline = "Most of your stack can be covered automatically — you're one setup away from continuous compliance.";
  } else if (score >= 40) {
    headline = "Good foundations, gaps to close";
    subline = "You have some tooling in place. Automating evidence collection is the next step to audit readiness.";
  } else {
    headline = "Time to build your foundation";
    subline = "You're earlier in the journey — TraceLayer gives you the structure and automation to get audit-ready fast.";
  }

  return { score, automatable, hoursPerWeek, headline, subline, insights };
}

// ── Score ring ────────────────────────────────────────────────────────────────

function ScoreRing({ score }: { score: number }) {
  const r = 52;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = score >= 70 ? "#10b981" : score >= 40 ? "#f59e0b" : "#0f766e";

  return (
    <div className="relative w-32 h-32 shrink-0">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r={r} fill="none" stroke="#e2e8f0" strokeWidth="10" />
        <circle
          cx="60" cy="60" r={r}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 1.2s ease-in-out" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-black text-gray-900">{score}%</span>
        <span className="text-[10px] text-gray-400 font-semibold uppercase tracking-wide">Automatable</span>
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function ComplianceQuiz() {
  const [step, setStep] = useState(-1); // -1 = intro
  const [answers, setAnswers] = useState<Answers>({});
  const [done, setDone] = useState(false);
  const [emailCaptured, setEmailCaptured] = useState(false);

  const q = QUESTIONS[step];
  const progress = step >= 0 ? ((step + 1) / QUESTIONS.length) * 100 : 0;

  const answer = answers[q?.id ?? ""] ?? (q?.type === "multi" ? [] : "");

  const toggleMulti = (val: string) => {
    const cur = (answers[q.id] as string[]) ?? [];
    setAnswers((a) => ({
      ...a,
      [q.id]: cur.includes(val) ? cur.filter((v) => v !== val) : [...cur, val],
    }));
  };

  const selectSingle = (val: string) => {
    setAnswers((a) => ({ ...a, [q.id]: val }));
  };

  const canNext = () => {
    if (!q) return false;
    if (q.type === "multi") return ((answers[q.id] as string[]) ?? []).length > 0;
    return !!answers[q.id];
  };

  const next = () => {
    if (step < QUESTIONS.length - 1) setStep((s) => s + 1);
    else setDone(true);
  };

  const reset = () => {
    setStep(-1);
    setAnswers({});
    setDone(false);
    setEmailCaptured(false);
  };

  const result = done ? computeResult(answers) : null;

  // ── Intro ──
  if (step === -1) {
    return (
      <div className="text-center">
        <div className="w-14 h-14 bg-white/10 rounded-2xl flex items-center justify-center mx-auto mb-5">
          <Zap className="w-7 h-7 text-white" />
        </div>
        <h2 className="text-2xl md:text-3xl font-extrabold text-white mb-3">
          Free compliance readiness check
        </h2>
        <p className="text-white/70 text-sm md:text-base max-w-md mx-auto mb-8 leading-relaxed">
          5 questions. 60 seconds. See exactly how much of your compliance work can be automated — and what to tackle first.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center items-center mb-6">
          <div className="flex items-center gap-2 text-white/60 text-xs"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> No sign-up required</div>
          <div className="flex items-center gap-2 text-white/60 text-xs"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Instant results</div>
          <div className="flex items-center gap-2 text-white/60 text-xs"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Personalized to your stack</div>
        </div>
        <button
          onClick={() => setStep(0)}
          className="inline-flex items-center gap-2 bg-white hover:bg-white/90 text-gray-900 font-bold px-8 py-3.5 rounded-xl transition-colors text-sm shadow-lg"
        >
          Start the check <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    );
  }

  // ── Email gate ──
  if (done && result && !emailCaptured) {
    return (
      <ToolEmailGate
        toolName="compliance-readiness-check"
        headline={result.headline}
        subline={result.subline}
        teasers={[
          {
            label: "automatable",
            value: `${result.score}%`,
            valueColor: result.score >= 70 ? "text-emerald-600" : result.score >= 40 ? "text-amber-600" : "text-teal-700",
          },
          {
            label: "integrations ready",
            value: String(result.automatable),
            valueColor: "text-gray-900",
          },
          ...(result.hoursPerWeek > 1
            ? [{ label: "hrs saved / week", value: `${result.hoursPerWeek}h+`, valueColor: "text-gray-900" }]
            : []),
        ]}
        onUnlocked={() => setEmailCaptured(true)}
      />
    );
  }

  // ── Results ──
  if (done && result) {
    return (
      <div className="max-w-2xl mx-auto">
        <p className="text-center text-white/60 text-xs font-semibold uppercase tracking-widest mb-6">Your results</p>
        <div className="bg-white rounded-2xl p-6 md:p-8 shadow-xl">
          <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6 mb-6">
            <ScoreRing score={result.score} />
            <div>
              <p className="text-lg font-extrabold text-gray-900 mb-1">{result.headline}</p>
              <p className="text-sm text-gray-500 leading-relaxed mb-3">{result.subline}</p>
              <div className="flex flex-wrap gap-3 text-xs">
                <div className="bg-slate-50 rounded-lg px-3 py-2 text-center">
                  <p className="font-bold text-gray-900 text-base">{result.automatable}</p>
                  <p className="text-gray-500">integrations ready</p>
                </div>
                {result.hoursPerWeek > 1 && (
                  <div className="bg-slate-50 rounded-lg px-3 py-2 text-center">
                    <p className="font-bold text-gray-900 text-base">{result.hoursPerWeek}h+</p>
                    <p className="text-gray-500">saved per week</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="space-y-3 mb-6">
            {result.insights.map((ins, i) => (
              <div key={i} className="flex items-start gap-3 text-sm">
                <div className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${
                  ins.type === "good" ? "bg-emerald-100" : ins.type === "warn" ? "bg-amber-100" : "bg-blue-100"
                }`}>
                  <div className={`w-2 h-2 rounded-full ${
                    ins.type === "good" ? "bg-emerald-500" : ins.type === "warn" ? "bg-amber-500" : "bg-blue-500"
                  }`} />
                </div>
                <p className="text-gray-700 leading-relaxed">{ins.text}</p>
              </div>
            ))}
          </div>

          <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-gray-100">
            <Link
              href="/register"
              className="flex-1 flex items-center justify-center gap-2 bg-slate-900 hover:bg-slate-800 text-white font-semibold py-3 rounded-xl transition-colors text-sm"
            >
              Start automating free <ArrowRight className="w-4 h-4" />
            </Link>
            <button
              onClick={reset}
              className="flex items-center justify-center gap-2 text-gray-500 hover:text-gray-700 text-sm font-medium px-4 py-3 rounded-xl border border-gray-200 hover:bg-gray-50 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" /> Retake
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Question ──
  return (
    <div className="max-w-2xl mx-auto">
      {/* Progress */}
      <div className="mb-6">
        <div className="flex items-center justify-between text-xs text-white/50 mb-2">
          <span>Question {step + 1} of {QUESTIONS.length}</span>
          <span>{Math.round(progress)}%</span>
        </div>
        <div className="h-1 bg-white/20 rounded-full overflow-hidden">
          <div
            className="h-full bg-white rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="bg-white rounded-2xl p-6 md:p-8 shadow-xl">
        <p className="font-extrabold text-gray-900 text-lg mb-5">{q.question}</p>

        {q.type === "single" && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 mb-6">
            {q.options.map((opt) => (
              <button
                key={opt.value}
                onClick={() => selectSingle(opt.value)}
                className={`text-left px-4 py-3 rounded-xl border-2 text-sm font-medium transition-all ${
                  answer === opt.value
                    ? "border-slate-900 bg-slate-900 text-white"
                    : "border-gray-200 text-gray-700 hover:border-gray-300 hover:bg-gray-50"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        )}

        {q.type === "multi" && (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2.5 mb-6">
            {q.options.map((opt) => {
              const selected = ((answer as string[]) ?? []).includes(opt.value);
              return (
                <button
                  key={opt.value}
                  onClick={() => toggleMulti(opt.value)}
                  className={`text-center px-3 py-3 rounded-xl border-2 text-sm font-semibold transition-all ${
                    selected
                      ? "border-slate-900 bg-slate-900 text-white"
                      : "border-gray-200 text-gray-700 hover:border-gray-300 hover:bg-gray-50"
                  }`}
                >
                  {selected && <CheckCircle2 className="w-3.5 h-3.5 mx-auto mb-1 text-emerald-400" />}
                  {opt.label}
                </button>
              );
            })}
          </div>
        )}

        <div className="flex items-center justify-between">
          <button
            onClick={() => setStep((s) => Math.max(-1, s - 1))}
            className="text-sm text-gray-400 hover:text-gray-600 transition-colors"
          >
            ← Back
          </button>
          <button
            onClick={next}
            disabled={!canNext()}
            className="flex items-center gap-2 bg-slate-900 hover:bg-slate-800 disabled:opacity-30 text-white font-semibold px-6 py-2.5 rounded-xl transition-colors text-sm"
          >
            {step === QUESTIONS.length - 1 ? "See my results" : "Next"} <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

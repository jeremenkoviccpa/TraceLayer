"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { api } from "@/lib/api";
import type { TrainingQuiz, TrainingQuizResult } from "@/lib/types";
import {
  GraduationCap, CheckCircle2, XCircle, AlertTriangle,
  ArrowRight, ChevronRight, Loader2, Award, RotateCcw,
} from "lucide-react";

export default function TrainingQuizPage() {
  const { token } = useParams<{ token: string }>();
  const router = useRouter();

  const [quiz, setQuiz] = useState<TrainingQuiz | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // answers: question id → chosen option index
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<TrainingQuizResult | null>(null);

  useEffect(() => {
    if (!token) return;
    api.getTrainingQuiz(token)
      .then((q) => {
        if (q.already_passed) {
          router.replace(`/training/certificate/${token}`);
          return;
        }
        setQuiz(q);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Training link not found"))
      .finally(() => setLoading(false));
  }, [token, router]);

  const allAnswered = quiz ? Object.keys(answers).length === quiz.questions.length : false;

  const handleSubmit = async () => {
    if (!quiz || !allAnswered) return;
    setSubmitting(true);
    try {
      const stringAnswers: Record<string, number> = {};
      Object.entries(answers).forEach(([k, v]) => { stringAnswers[String(k)] = v; });
      const res = await api.submitTrainingQuiz(token, stringAnswers);
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Submission failed");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRetake = () => {
    setResult(null);
    setAnswers({});
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-teal-500 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-sm text-center">
          <div className="w-14 h-14 bg-red-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <AlertTriangle className="w-7 h-7 text-red-500" />
          </div>
          <h1 className="text-xl font-bold text-gray-900 mb-2">Link unavailable</h1>
          <p className="text-sm text-gray-500">{error}</p>
        </div>
      </div>
    );
  }

  if (!quiz) return null;

  // ── Result screen ──────────────────────────────────────────────────────────
  if (result) {
    const passed = result.passed;
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col font-[family:'Sora',_ui-sans-serif,_system-ui]">
        <header className="bg-white border-b border-gray-100">
          <div className="max-w-2xl mx-auto px-6 h-14 flex items-center gap-2.5">
            <Image src="/logo-icon.png" alt="TraceLayer" width={26} height={26} className="rounded-lg" />
            <span className="font-extrabold text-sm text-gray-900">TraceLayer</span>
          </div>
        </header>

        <main className="flex-1 flex items-center justify-center p-6">
          <div className="max-w-md w-full text-center">
            <div className={`w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6 ${passed ? "bg-emerald-100" : "bg-red-50"}`}>
              {passed
                ? <CheckCircle2 className="w-10 h-10 text-emerald-500" />
                : <XCircle className="w-10 h-10 text-red-400" />
              }
            </div>

            <h1 className="text-2xl font-extrabold text-gray-900 mb-2">
              {passed ? "You passed!" : "Not quite — try again"}
            </h1>

            <p className="text-gray-500 text-sm mb-6">
              {passed
                ? `You scored ${result.score}% (${result.correct}/${result.total} correct). Your certificate is ready.`
                : `You scored ${result.score}% (${result.correct}/${result.total} correct). You need 80% to pass.`
              }
            </p>

            {/* Score ring */}
            <div className="flex items-center justify-center mb-8">
              <div className="relative w-28 h-28">
                <svg className="w-full h-full -rotate-90" viewBox="0 0 84 84">
                  <circle cx="42" cy="42" r="36" fill="none" stroke="#f1f5f9" strokeWidth="8" />
                  <circle
                    cx="42" cy="42" r="36"
                    fill="none"
                    stroke={passed ? "#10b981" : "#ef4444"}
                    strokeWidth="8"
                    strokeDasharray={2 * Math.PI * 36}
                    strokeDashoffset={2 * Math.PI * 36 - (result.score / 100) * 2 * Math.PI * 36}
                    strokeLinecap="round"
                    style={{ transition: "stroke-dashoffset 1s ease-in-out" }}
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className={`text-2xl font-black ${passed ? "text-emerald-500" : "text-red-400"}`}>{result.score}%</span>
                </div>
              </div>
            </div>

            {passed ? (
              <div className="space-y-3">
                <Link
                  href={`/training/certificate/${token}`}
                  className="flex items-center justify-center gap-2 w-full bg-teal-600 hover:bg-teal-700 text-white font-bold px-6 py-3 rounded-xl text-sm transition-colors"
                >
                  <Award className="w-4 h-4" /> View & Download Certificate
                </Link>
                <p className="text-xs text-gray-400">
                  Your completion has been recorded and evidence automatically filed.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                <button
                  onClick={handleRetake}
                  className="flex items-center justify-center gap-2 w-full bg-gray-900 hover:bg-gray-800 text-white font-bold px-6 py-3 rounded-xl text-sm transition-colors"
                >
                  <RotateCcw className="w-4 h-4" /> Retake Quiz
                </button>
                <p className="text-xs text-gray-400">Review the material and try again. You need 80% to pass.</p>
              </div>
            )}
          </div>
        </main>

        <style jsx global>{`
          @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&display=swap');
        `}</style>
      </div>
    );
  }

  // ── Quiz screen ────────────────────────────────────────────────────────────
  const answered = Object.keys(answers).length;
  const total = quiz.questions.length;

  return (
    <div className="min-h-screen bg-gray-50 font-[family:'Sora',_ui-sans-serif,_system-ui]">
      <header className="bg-white border-b border-gray-100 sticky top-0 z-10">
        <div className="max-w-2xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Image src="/logo-icon.png" alt="TraceLayer" width={26} height={26} className="rounded-lg" />
            <span className="font-extrabold text-sm text-gray-900">TraceLayer</span>
          </div>
          <div className="text-xs text-gray-400 font-medium">{answered}/{total} answered</div>
        </div>
        {/* Progress bar */}
        <div className="h-1 bg-gray-100">
          <div
            className="h-full bg-teal-500 transition-all duration-300"
            style={{ width: `${(answered / total) * 100}%` }}
          />
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
        {/* Title */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-xl bg-teal-100 flex items-center justify-center">
              <GraduationCap className="w-4 h-4 text-teal-600" />
            </div>
            <span className="text-xs font-semibold text-teal-600 uppercase tracking-widest">Security Training</span>
          </div>
          <h1 className="text-xl font-extrabold text-gray-900">{quiz.title}</h1>
          <p className="text-sm text-gray-500 mt-1">
            Hi {quiz.assignee_name || quiz.assignee_email.split("@")[0]}! Answer all {total} questions. You need 80% to pass.
          </p>
        </div>

        {/* Questions */}
        <div className="space-y-5 mb-8">
          {quiz.questions.map((q, qi) => (
            <div key={q.id} className={`bg-white rounded-2xl border p-5 transition-all ${answers[q.id] !== undefined ? "border-teal-200 shadow-sm" : "border-gray-100"}`}>
              <div className="flex items-start gap-3 mb-4">
                <span className={`shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold mt-0.5 ${answers[q.id] !== undefined ? "bg-teal-500 text-white" : "bg-gray-100 text-gray-400"}`}>
                  {answers[q.id] !== undefined ? "✓" : qi + 1}
                </span>
                <p className="text-sm font-semibold text-gray-900 leading-relaxed">{q.question}</p>
              </div>
              <div className="space-y-2 ml-9">
                {q.options.map((opt, oi) => {
                  const selected = answers[q.id] === oi;
                  return (
                    <button
                      key={oi}
                      onClick={() => setAnswers((prev) => ({ ...prev, [q.id]: oi }))}
                      className={`w-full text-left flex items-center gap-3 px-4 py-3 rounded-xl border text-sm transition-all ${
                        selected
                          ? "bg-teal-600 border-teal-600 text-white font-semibold shadow-sm"
                          : "bg-gray-50 border-gray-100 text-gray-700 hover:border-teal-200 hover:bg-teal-50"
                      }`}
                    >
                      <span className={`w-5 h-5 rounded-full border-2 shrink-0 flex items-center justify-center ${selected ? "border-white bg-white/20" : "border-gray-300"}`}>
                        {selected && <span className="w-2 h-2 rounded-full bg-white" />}
                      </span>
                      {opt}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Submit */}
        <div className="sticky bottom-4">
          <button
            onClick={handleSubmit}
            disabled={!allAnswered || submitting}
            className="w-full flex items-center justify-center gap-2 bg-teal-600 hover:bg-teal-700 text-white font-bold px-6 py-3.5 rounded-2xl text-sm transition-all shadow-lg shadow-teal-600/25 disabled:opacity-40 disabled:shadow-none"
          >
            {submitting ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> Submitting…</>
            ) : (
              <>{allAnswered ? "Submit Quiz" : `Answer all questions (${total - answered} remaining)`} <ChevronRight className="w-4 h-4" /></>
            )}
          </button>
        </div>
      </main>

      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&display=swap');
      `}</style>
    </div>
  );
}

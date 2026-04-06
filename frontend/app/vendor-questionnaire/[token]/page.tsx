"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetchQuestionnaire(token: string) {
  const res = await fetch(`${API_URL}/v1/vendor-questionnaires/public/${token}`);
  if (!res.ok) throw new Error("Not found");
  return res.json();
}

async function submitResponses(token: string, responses: Record<string, string>, contactName: string) {
  const res = await fetch(`${API_URL}/v1/vendor-questionnaires/public/${token}/respond`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ responses, vendor_contact_name: contactName }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Submission failed");
  }
  return res.json();
}

export default function VendorQuestionnairePage() {
  const params = useParams();
  const token = params?.token as string;
  const [data, setData] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [responses, setResponses] = useState<Record<string, string>>({});
  const [contactName, setContactName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    if (!token) return;
    fetchQuestionnaire(token).then(d => {
      setData(d);
      if (d.already_completed) setSubmitted(true);
    }).catch(() => setError("This questionnaire link is invalid or has expired."));
  }, [token]);

  const handleSubmit = async () => {
    const answered = data?.questions?.filter((q: any) => responses[q.id]?.trim()).length ?? 0;
    const required = data?.questions?.filter((q: any) => q.required).length ?? 0;
    if (answered < required) {
      alert("Please answer all required questions before submitting.");
      return;
    }
    setSubmitting(true);
    try {
      await submitResponses(token, responses, contactName);
      setSubmitted(true);
    } catch (e: any) {
      alert(e.message || "Submission failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  if (error) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-lg p-8 max-w-md w-full text-center">
        <div className="w-12 h-12 bg-red-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <svg className="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        </div>
        <p className="font-semibold text-gray-800">{error}</p>
      </div>
    </div>
  );

  if (!data) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-teal-500 border-t-transparent" />
    </div>
  );

  if (submitted) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-lg p-8 max-w-md w-full text-center">
        <div className="w-12 h-12 bg-emerald-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <svg className="w-6 h-6 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
        </div>
        <h2 className="text-xl font-bold text-gray-900 mb-2">Questionnaire submitted</h2>
        <p className="text-gray-500 text-sm">Thank you. Your responses have been sent to <strong>{data.company_name}</strong> and will be reviewed by their security team.</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-teal-50 flex items-center justify-center">
              <svg className="w-5 h-5 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Security Questionnaire</p>
              <h1 className="text-lg font-bold text-gray-900">Sent by {data.company_name}</h1>
            </div>
          </div>
          <p className="text-sm text-gray-500">
            Please complete the {data.questions?.length} questions below. Your responses will help {data.company_name} assess your security posture as part of their vendor risk management process.
          </p>
          {data.due_date && (
            <div className="mt-3 flex items-center gap-1.5 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2">
              <svg className="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              Due by {new Date(data.due_date).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}
            </div>
          )}
        </div>

        {/* Contact */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <label className="block text-sm font-semibold text-gray-700 mb-2">Your name / contact <span className="text-gray-400 font-normal">(optional)</span></label>
          <input
            type="text"
            value={contactName}
            onChange={e => setContactName(e.target.value)}
            placeholder="Jane Smith, Head of Security"
            className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30"
          />
        </div>

        {/* Questions */}
        {data.questions?.map((q: any, idx: number) => (
          <div key={q.id} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <div className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-teal-50 text-teal-600 text-xs font-bold flex items-center justify-center mt-0.5">{idx + 1}</span>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-800 leading-relaxed mb-3">
                  {q.text}
                  {q.required && <span className="text-red-400 ml-1">*</span>}
                </p>
                <textarea
                  value={responses[q.id] ?? ""}
                  onChange={e => setResponses(prev => ({ ...prev, [q.id]: e.target.value }))}
                  rows={4}
                  placeholder="Your response…"
                  className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30 resize-none"
                />
              </div>
            </div>
          </div>
        ))}

        {/* Submit */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <p className="text-xs text-gray-400 mb-4">
            By submitting, you confirm that the information provided is accurate to the best of your knowledge. Your responses will be shared only with {data.company_name}.
          </p>
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="w-full bg-teal-600 hover:bg-teal-700 text-white font-semibold py-3 rounded-xl transition-colors disabled:opacity-50 text-sm"
          >
            {submitting ? "Submitting…" : "Submit Security Questionnaire"}
          </button>
        </div>
      </div>
    </div>
  );
}

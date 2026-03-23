"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Image from "next/image";
import { api } from "@/lib/api";
import type { TrainingCertificate } from "@/lib/types";
import { Download, ShieldCheck, AlertTriangle, Loader2, Award } from "lucide-react";

export default function TrainingCertificatePage() {
  const { token } = useParams<{ token: string }>();
  const [cert, setCert] = useState<TrainingCertificate | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    api.getTrainingCertificate(token)
      .then(setCert)
      .catch((e) => setError(e instanceof Error ? e.message : "Certificate not found"))
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-teal-500 animate-spin" />
      </div>
    );
  }

  if (error || !cert) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="text-center max-w-sm">
          <div className="w-14 h-14 bg-red-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <AlertTriangle className="w-7 h-7 text-red-500" />
          </div>
          <h1 className="text-xl font-bold text-gray-900 mb-2">Certificate unavailable</h1>
          <p className="text-sm text-gray-500">{error ?? "This training has not been completed yet."}</p>
        </div>
      </div>
    );
  }

  const completedDate = new Date(cert.completed_at).toLocaleDateString("en-GB", {
    day: "numeric", month: "long", year: "numeric",
  });

  return (
    <>
      {/* ── Screen shell (hidden on print) ── */}
      <div className="min-h-screen bg-gradient-to-br from-slate-100 via-gray-50 to-teal-50 print:hidden flex flex-col font-[family:'Sora',_ui-sans-serif,_system-ui]">
        <div className="max-w-3xl mx-auto w-full px-4 py-6">
          {/* Toolbar */}
          <div className="flex items-center justify-between mb-6 no-print">
            <div className="flex items-center gap-2">
              <Image src="/logo-icon.png" alt="TraceLayer" width={26} height={26} className="rounded-lg" />
              <span className="font-extrabold text-sm text-gray-900">TraceLayer</span>
            </div>
            <button
              onClick={() => window.print()}
              className="flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold px-4 py-2 rounded-xl text-sm transition-colors"
            >
              <Download className="w-4 h-4" /> Download PDF
            </button>
          </div>

          {/* Certificate preview card */}
          <div className="bg-white rounded-3xl shadow-2xl shadow-gray-200/80 overflow-hidden">
            <CertificateContent cert={cert} completedDate={completedDate} />
          </div>

          <p className="text-center text-xs text-gray-400 mt-4">
            Click "Download PDF" to save this certificate. Your browser will open a print dialog — select "Save as PDF".
          </p>
        </div>
      </div>

      {/* ── Print-only version (fills the page exactly) ── */}
      <div className="hidden print:block">
        <CertificateContent cert={cert} completedDate={completedDate} />
      </div>

      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700;800;900&display=swap');

        @media print {
          * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
          @page { size: A4 landscape; margin: 0; }
          body { margin: 0; padding: 0; font-family: 'Sora', sans-serif; }
        }
      `}</style>
    </>
  );
}

function CertificateContent({ cert, completedDate }: { cert: TrainingCertificate; completedDate: string }) {
  return (
    <div
      className="relative w-full overflow-hidden print:h-screen"
      style={{
        background: "linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f2a1e 100%)",
        minHeight: "560px",
        fontFamily: "'Sora', ui-sans-serif, system-ui",
      }}
    >
      {/* Decorative background rings */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-32 -right-32 w-96 h-96 rounded-full border border-teal-500/10" />
        <div className="absolute -top-20 -right-20 w-72 h-72 rounded-full border border-teal-500/10" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 rounded-full border border-emerald-500/10" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] rounded-full border border-white/[0.03]" />
        {/* Gold accent line top */}
        <div className="absolute top-0 left-0 right-0 h-1" style={{ background: "linear-gradient(90deg, #0f766e, #10b981, #0f766e)" }} />
        {/* Gold accent line bottom */}
        <div className="absolute bottom-0 left-0 right-0 h-1" style={{ background: "linear-gradient(90deg, #0f766e, #10b981, #0f766e)" }} />
      </div>

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center justify-center px-8 py-12 text-center min-h-[560px]">

        {/* Seal */}
        <div className="relative mb-6">
          <div className="w-20 h-20 rounded-full flex items-center justify-center" style={{ background: "linear-gradient(135deg, #0f766e, #10b981)" }}>
            <Award className="w-10 h-10 text-white" />
          </div>
          <div className="absolute inset-0 rounded-full" style={{ boxShadow: "0 0 0 4px rgba(16,185,129,0.2), 0 0 0 8px rgba(16,185,129,0.08)" }} />
        </div>

        {/* Issuer */}
        <div className="flex items-center gap-2 mb-4">
          <Image src="/logo-icon.png" alt="TraceLayer" width={18} height={18} className="rounded-md opacity-80" />
          <p className="text-teal-400 text-xs font-semibold uppercase tracking-[0.2em]">TraceLayer · Certificate of Completion</p>
        </div>

        {/* Main headline */}
        <h1 className="text-white text-4xl font-black mb-2 leading-tight" style={{ textShadow: "0 2px 20px rgba(0,0,0,0.5)" }}>
          {cert.title}
        </h1>

        <div className="w-24 h-px my-5" style={{ background: "linear-gradient(90deg, transparent, #10b981, transparent)" }} />

        <p className="text-slate-400 text-sm uppercase tracking-widest mb-2">This certifies that</p>

        <h2 className="text-white text-3xl font-extrabold mb-1">{cert.assignee_name}</h2>
        <p className="text-slate-400 text-sm mb-6">{cert.assignee_email}</p>

        <p className="text-slate-300 text-sm max-w-lg leading-relaxed mb-6">
          has successfully completed the <span className="text-white font-semibold">{cert.title}</span> course
          on behalf of <span className="text-teal-400 font-semibold">{cert.company_name}</span>,
          demonstrating competency with a score of{" "}
          <span className="text-emerald-400 font-bold">{cert.score}%</span>.
        </p>

        {/* Meta row */}
        <div className="flex items-center gap-6 text-xs text-slate-500">
          <div className="text-center">
            <p className="text-slate-300 font-semibold text-sm">{completedDate}</p>
            <p className="text-slate-500 mt-0.5">Date of Completion</p>
          </div>
          <div className="w-px h-8 bg-slate-700" />
          <div className="text-center">
            <p className="text-emerald-400 font-bold text-sm">{cert.score}%</p>
            <p className="text-slate-500 mt-0.5">Score Achieved</p>
          </div>
          <div className="w-px h-8 bg-slate-700" />
          <div className="text-center">
            <p className="text-slate-300 font-semibold text-sm">{cert.company_name}</p>
            <p className="text-slate-500 mt-0.5">Organisation</p>
          </div>
        </div>

        {/* Compliance badges */}
        <div className="flex items-center gap-3 mt-8">
          {["SOC 2 CC1.4", "ISO 27001 A.7.2.2", "HIPAA §164.308"].map((badge) => (
            <div key={badge} className="flex items-center gap-1.5 bg-white/5 border border-white/10 rounded-full px-3 py-1">
              <ShieldCheck className="w-3 h-3 text-teal-400" />
              <span className="text-[10px] font-semibold text-slate-400">{badge}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

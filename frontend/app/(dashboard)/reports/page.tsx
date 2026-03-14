"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Report } from "@/lib/types";
import { FileText, Download, Clock, CheckCircle2, AlertCircle, Plus } from "lucide-react";

function statusIcon(status: string) {
  if (status === "complete") return <CheckCircle2 className="w-4 h-4 text-green-500" />;
  if (status === "error") return <AlertCircle className="w-4 h-4 text-red-500" />;
  return <Clock className="w-4 h-4 text-yellow-500 animate-pulse" />;
}

function statusLabel(status: string) {
  if (status === "complete") return "Complete";
  if (status === "error") return "Failed";
  return "Generating…";
}

const FRAMEWORKS = [
  { value: "soc2", label: "SOC 2" },
  { value: "iso27001", label: "ISO 27001" },
  { value: "hipaa", label: "HIPAA" },
];

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [toast, setToast] = useState("");
  const [framework, setFramework] = useState("soc2");
  const [format, setFormat] = useState("json");

  const load = () =>
    api
      .getReports()
      .then((p) => setReports(p.items))
      .catch(console.error)
      .finally(() => setLoading(false));

  useEffect(() => {
    load();
  }, []);

  // Poll every 3s while any report is pending
  useEffect(() => {
    const hasPending = reports.some((r) => r.status === "pending");
    if (!hasPending) return;
    const timer = setInterval(load, 3000);
    return () => clearInterval(timer);
  }, [reports]);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(""), 3000);
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await api.generateReport(framework, "full", format);
      await load();
      showToast("Report generation started");
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Failed to generate report");
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = async (report: Report) => {
    if (report.status !== "complete") return;
    setDownloading(report.id);
    try {
      const { url, file_name } = await api.downloadReport(report.id);
      const a = document.createElement("a");
      a.href = url;
      a.download = file_name ?? `tracelayer-report-${report.id.slice(0, 8)}.${report.fmt}`;
      a.target = "_blank";
      a.click();
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Download failed");
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div>
      {toast && (
        <div className="fixed top-4 right-4 bg-gray-900 text-white text-sm px-4 py-2 rounded-lg shadow-lg z-50">
          {toast}
        </div>
      )}

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
        <div className="flex items-center gap-2 flex-wrap">
          <select
            value={framework}
            onChange={(e) => setFramework(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            {FRAMEWORKS.map((f) => (
              <option key={f.value} value={f.value}>{f.label}</option>
            ))}
          </select>
          <div className="flex rounded-lg border border-gray-300 overflow-hidden text-sm">
            {["json", "pdf"].map((fmt) => (
              <button
                key={fmt}
                onClick={() => setFormat(fmt)}
                className={`px-3 py-2 font-medium transition-colors ${
                  format === fmt
                    ? "bg-brand-600 text-white"
                    : "text-gray-600 hover:bg-gray-50"
                }`}
              >
                {fmt.toUpperCase()}
              </button>
            ))}
          </div>
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            {generating ? "Generating…" : "Generate report"}
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : reports.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <FileText className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 text-sm">No reports generated yet.</p>
          <p className="text-gray-400 text-xs mt-1">
            Collect evidence first, then generate a report.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {reports.map((r) => (
            <div
              key={r.id}
              className="bg-white rounded-xl border border-gray-200 p-4 md:p-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="flex items-center gap-3 md:gap-4">
                <FileText className="w-8 h-8 text-gray-300 shrink-0" />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900 uppercase text-sm">{r.framework}</span>
                    <span className="text-gray-400 text-sm">—</span>
                    <span className="text-gray-600 text-sm capitalize">{r.report_type}</span>
                    <div className="flex items-center gap-1 ml-1">
                      {statusIcon(r.status)}
                      <span className="text-xs text-gray-500">{statusLabel(r.status)}</span>
                    </div>
                  </div>
                  <div className="text-xs text-gray-400 mt-0.5">
                    Created {new Date(r.created_at).toLocaleString()}
                    {r.generated_at && (
                      <> · Generated {new Date(r.generated_at).toLocaleString()}</>
                    )}
                  </div>
                </div>
              </div>

              {r.status === "complete" && (
                <button
                  onClick={() => handleDownload(r)}
                  disabled={downloading === r.id}
                  className="flex items-center gap-1.5 px-3 py-1.5 border border-gray-300 text-gray-700 hover:bg-gray-50 text-sm rounded-lg transition-colors disabled:opacity-40 self-start sm:self-auto shrink-0"
                >
                  <Download className="w-4 h-4" />
                  {downloading === r.id ? "Downloading…" : `Download ${r.fmt.toUpperCase()}`}
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

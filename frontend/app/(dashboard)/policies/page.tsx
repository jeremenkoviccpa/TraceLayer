"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Policy } from "@/lib/types";
import { FileText, Save, CheckCircle2, Clock } from "lucide-react";

export default function PoliciesPage() {
  const [policies, setPolicies]   = useState<Policy[]>([]);
  const [selected, setSelected]   = useState<Policy | null>(null);
  const [content, setContent]     = useState("");
  const [loading, setLoading]     = useState(true);
  const [saving, setSaving]       = useState(false);
  const [saved, setSaved]         = useState(false);

  useEffect(() => {
    api.getPolicies()
      .then((ps) => {
        setPolicies(ps);
        if (ps.length > 0) { setSelected(ps[0]); setContent(ps[0].content); }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const selectPolicy = (p: Policy) => {
    setSelected(p);
    setContent(p.content);
    setSaved(false);
  };

  const handleSave = async () => {
    if (!selected) return;
    setSaving(true);
    try {
      const updated = await api.savePolicy(selected.slug, content);
      setPolicies((prev) => prev.map((p) => p.slug === updated.slug ? { ...p, ...updated } : p));
      setSelected((prev) => prev ? { ...prev, ...updated } : prev);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch { /* ignore */ } finally { setSaving(false); }
  };

  const wordCount = content.trim().split(/\s+/).filter(Boolean).length;

  return (
    <div className="animate-fade-in h-full">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Policy Templates</h1>
          <p className="text-sm text-gray-500 mt-0.5">Pre-written SOC 2 & ISO 27001 policies. Customize and adopt in one click.</p>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <div className="flex gap-5 h-[calc(100vh-13rem)]">
          {/* Sidebar */}
          <div className="w-56 shrink-0 space-y-0.5 overflow-y-auto">
            {policies.map((p) => (
              <button
                key={p.slug}
                onClick={() => selectPolicy(p)}
                className={`w-full text-left px-3 py-2.5 rounded-xl text-sm transition-all ${
                  selected?.slug === p.slug
                    ? "bg-brand-600 text-white font-semibold shadow-sm"
                    : "text-gray-600 hover:bg-white hover:text-gray-900 hover:shadow-sm"
                }`}
              >
                <div className="flex items-center gap-2">
                  <FileText className={`w-3.5 h-3.5 shrink-0 ${selected?.slug === p.slug ? "text-white/80" : "text-gray-400"}`} />
                  <span className="leading-snug line-clamp-2">{p.title}</span>
                </div>
                {p.updated_at && (
                  <p className={`text-[10px] mt-0.5 ml-5.5 ${selected?.slug === p.slug ? "text-white/60" : "text-gray-400"}`}>
                    Saved
                  </p>
                )}
              </button>
            ))}
          </div>

          {/* Editor */}
          {selected && (
            <div className="flex-1 flex flex-col bg-white rounded-2xl border border-gray-100 shadow-card overflow-hidden">
              <div className="flex items-center justify-between px-5 py-3.5 border-b border-gray-100 shrink-0">
                <div>
                  <h2 className="font-bold text-gray-900 text-sm">{selected.title}</h2>
                  <p className="text-xs text-gray-400">{selected.category}</p>
                </div>
                <div className="flex items-center gap-3">
                  {selected.updated_at && (
                    <span className="hidden sm:flex items-center gap-1 text-xs text-gray-400">
                      <Clock className="w-3 h-3" />
                      Last saved {new Date(selected.updated_at).toLocaleDateString()}
                    </span>
                  )}
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="flex items-center gap-1.5 text-sm font-semibold px-3.5 py-2 rounded-xl transition-colors disabled:opacity-50 bg-brand-600 hover:bg-brand-700 text-white"
                  >
                    {saved
                      ? <><CheckCircle2 className="w-3.5 h-3.5" /> Saved</>
                      : saving
                        ? "Saving…"
                        : <><Save className="w-3.5 h-3.5" /> Save policy</>
                    }
                  </button>
                </div>
              </div>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                className="flex-1 w-full px-5 py-4 text-sm text-gray-800 leading-relaxed resize-none focus:outline-none font-mono"
                spellCheck={false}
              />
              <div className="px-5 py-2 border-t border-gray-100 flex items-center justify-between">
                <p className="text-xs text-gray-400">{wordCount} words</p>
                <p className="text-xs text-gray-400">Plain text — copy into your policy doc or wiki</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

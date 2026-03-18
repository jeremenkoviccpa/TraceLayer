"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { SoaItem } from "@/lib/types";
import { BookCheck, ChevronDown, ChevronUp, Save, X } from "lucide-react";

const THEMES = ["All", "Organizational", "People", "Physical", "Technological"] as const;
const STATUSES = ["not_started", "in_progress", "implemented", "not_applicable"] as const;

const STATUS_STYLES: Record<string, string> = {
  not_started:    "bg-gray-100 text-gray-500",
  in_progress:    "bg-amber-100 text-amber-700",
  implemented:    "bg-emerald-100 text-emerald-700",
  not_applicable: "bg-gray-100 text-gray-400 line-through",
};

const STATUS_LABELS: Record<string, string> = {
  not_started:    "Not Started",
  in_progress:    "In Progress",
  implemented:    "Implemented",
  not_applicable: "N/A",
};

export default function SoaPage() {
  const [items, setItems]             = useState<SoaItem[]>([]);
  const [loading, setLoading]         = useState(true);
  const [themeFilter, setThemeFilter] = useState<typeof THEMES[number]>("All");
  const [inclFilter, setInclFilter]   = useState<"all" | "included" | "excluded">("all");
  const [expandedId, setExpandedId]   = useState<string | null>(null);
  const [editForm, setEditForm]       = useState<Partial<SoaItem>>({});
  const [saving, setSaving]           = useState(false);

  useEffect(() => {
    api.getSoa().then(async (data) => {
      if (data.length === 0) {
        const seeded = await api.initializeSoa();
        setItems(seeded);
      } else {
        setItems(data);
      }
    }).finally(() => setLoading(false));
  }, []);

  const filtered = items.filter((item) => {
    if (themeFilter !== "All" && item.annex_theme !== themeFilter) return false;
    if (inclFilter === "included" && !item.included) return false;
    if (inclFilter === "excluded" && item.included) return false;
    return true;
  });

  const toggleExpand = (item: SoaItem) => {
    if (expandedId === item.id) {
      setExpandedId(null);
      setEditForm({});
    } else {
      setExpandedId(item.id);
      setEditForm({
        included: item.included,
        justification: item.justification ?? "",
        implementation_status: item.implementation_status,
        implementation_notes: item.implementation_notes ?? "",
      });
    }
  };

  const handleSave = async (item: SoaItem) => {
    setSaving(true);
    try {
      const updated = await api.updateSoaItem(item.id, editForm);
      setItems((prev) => prev.map((i) => (i.id === updated.id ? updated : i)));
      setExpandedId(null);
      setEditForm({});
    } catch { /**/ } finally { setSaving(false); }
  };

  const toggleIncluded = async (item: SoaItem) => {
    const updated = await api.updateSoaItem(item.id, { included: !item.included });
    setItems((prev) => prev.map((i) => (i.id === updated.id ? updated : i)));
  };

  const totalIncluded    = items.filter((i) => i.included).length;
  const totalImplemented = items.filter((i) => i.implementation_status === "implemented").length;
  const totalInProgress  = items.filter((i) => i.implementation_status === "in_progress").length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const ExpandedForm = ({ item }: { item: SoaItem }) => (
    <div className="px-4 py-4 bg-gray-50 border-t border-gray-100">
      <div className="space-y-3 max-w-2xl">
        <div>
          <label className="text-xs font-medium text-gray-500 block mb-1">Implementation Status</label>
          <select
            value={editForm.implementation_status ?? item.implementation_status}
            onChange={(e) => setEditForm((f) => ({ ...f, implementation_status: e.target.value }))}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            {STATUSES.map((s) => (
              <option key={s} value={s}>{STATUS_LABELS[s]}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs font-medium text-gray-500 block mb-1">Justification</label>
          <textarea
            value={editForm.justification ?? ""}
            onChange={(e) => setEditForm((f) => ({ ...f, justification: e.target.value }))}
            rows={2}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
            placeholder="Why is this control included / excluded?"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-gray-500 block mb-1">Implementation Notes</label>
          <textarea
            value={editForm.implementation_notes ?? ""}
            onChange={(e) => setEditForm((f) => ({ ...f, implementation_notes: e.target.value }))}
            rows={2}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
            placeholder="How is this control implemented?"
          />
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => handleSave(item)}
            disabled={saving}
            className="flex items-center gap-1.5 bg-brand-600 text-white text-xs font-semibold px-3 py-2 rounded-lg hover:bg-brand-700 disabled:opacity-60 transition-colors"
          >
            <Save className="w-3.5 h-3.5" /> Save
          </button>
          <button
            onClick={() => { setExpandedId(null); setEditForm({}); }}
            className="flex items-center gap-1.5 text-gray-500 text-xs font-medium px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <X className="w-3.5 h-3.5" /> Cancel
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2.5">
          <BookCheck className="w-6 h-6 text-brand-600" />
          Statement of Applicability
        </h1>
        <p className="text-sm text-gray-500 mt-1">ISO 27001:2022 · 93 Annex A Controls</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-white rounded-2xl border border-gray-100 p-3 sm:p-4 text-center">
          <p className="text-xl sm:text-2xl font-bold text-gray-900">{totalIncluded}<span className="text-sm font-normal text-gray-400">/93</span></p>
          <p className="text-[11px] sm:text-xs text-gray-500 mt-1">Included</p>
        </div>
        <div className="bg-white rounded-2xl border border-gray-100 p-3 sm:p-4 text-center">
          <p className="text-xl sm:text-2xl font-bold text-emerald-600">{totalImplemented}</p>
          <p className="text-[11px] sm:text-xs text-gray-500 mt-1">Implemented</p>
        </div>
        <div className="bg-white rounded-2xl border border-gray-100 p-3 sm:p-4 text-center">
          <p className="text-xl sm:text-2xl font-bold text-amber-600">{totalInProgress}</p>
          <p className="text-[11px] sm:text-xs text-gray-500 mt-1">In Progress</p>
        </div>
      </div>

      {/* Filters — horizontally scrollable on mobile */}
      <div className="flex flex-col sm:flex-row gap-2">
        <div className="overflow-x-auto no-scrollbar">
          <div className="flex gap-1 bg-white border border-gray-100 rounded-xl p-1 w-max">
            {THEMES.map((t) => (
              <button
                key={t}
                onClick={() => setThemeFilter(t)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors whitespace-nowrap ${
                  themeFilter === t ? "bg-brand-600 text-white" : "text-gray-500 hover:bg-gray-50"
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
        <div className="flex gap-1 bg-white border border-gray-100 rounded-xl p-1 self-start">
          {(["all", "included", "excluded"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setInclFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors ${
                inclFilter === f ? "bg-brand-600 text-white" : "text-gray-500 hover:bg-gray-50"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Table — desktop */}
      <div className="hidden sm:block bg-white rounded-2xl border border-gray-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 text-xs text-gray-400 uppercase tracking-wider">
                <th className="px-4 py-3 text-left w-16">Ref</th>
                <th className="px-4 py-3 text-left">Control</th>
                <th className="px-4 py-3 text-left w-36">Status</th>
                <th className="px-4 py-3 text-center w-24">Included</th>
                <th className="px-4 py-3 text-right w-20">Edit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {filtered.map((item) => (
                <>
                  <tr key={item.id} className={`hover:bg-gray-50 transition-colors ${!item.included ? "opacity-50" : ""}`}>
                    <td className="px-4 py-3 font-mono text-xs text-gray-400">{item.annex_ref}</td>
                    <td className="px-4 py-3 text-gray-700">{item.title}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[item.implementation_status] ?? "bg-gray-100 text-gray-500"}`}>
                        {STATUS_LABELS[item.implementation_status] ?? item.implementation_status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button
                        onClick={() => toggleIncluded(item)}
                        className={`w-8 h-5 rounded-full transition-colors relative ${item.included ? "bg-brand-600" : "bg-gray-200"}`}
                      >
                        <span className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-all ${item.included ? "left-3.5" : "left-0.5"}`} />
                      </button>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => toggleExpand(item)}
                        className="text-gray-400 hover:text-gray-700 p-1 rounded-lg hover:bg-gray-100 transition-colors"
                      >
                        {expandedId === item.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </button>
                    </td>
                  </tr>
                  {expandedId === item.id && (
                    <tr key={`${item.id}-expand`}>
                      <td colSpan={5} className="p-0">
                        <ExpandedForm item={item} />
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
        {filtered.length === 0 && (
          <div className="text-center py-16 text-gray-400">
            <BookCheck className="w-10 h-10 mx-auto mb-3 opacity-30" />
            <p className="text-sm">No controls match the current filter.</p>
          </div>
        )}
      </div>

      {/* Card list — mobile */}
      <div className="sm:hidden space-y-2">
        {filtered.length === 0 && (
          <div className="text-center py-16 text-gray-400 bg-white rounded-2xl border border-gray-100">
            <BookCheck className="w-10 h-10 mx-auto mb-3 opacity-30" />
            <p className="text-sm">No controls match the current filter.</p>
          </div>
        )}
        {filtered.map((item) => (
          <div key={item.id} className={`bg-white rounded-2xl border border-gray-100 overflow-hidden ${!item.included ? "opacity-50" : ""}`}>
            <div className="flex items-start gap-3 p-4">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-mono text-[10px] text-gray-400 shrink-0">{item.annex_ref}</span>
                  <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-medium ${STATUS_STYLES[item.implementation_status] ?? "bg-gray-100 text-gray-500"}`}>
                    {STATUS_LABELS[item.implementation_status] ?? item.implementation_status}
                  </span>
                </div>
                <p className="text-sm font-medium text-gray-700 leading-snug">{item.title}</p>
              </div>
              <div className="flex items-center gap-2 shrink-0 mt-0.5">
                <button
                  onClick={() => toggleIncluded(item)}
                  className={`w-8 h-5 rounded-full transition-colors relative ${item.included ? "bg-brand-600" : "bg-gray-200"}`}
                >
                  <span className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-all ${item.included ? "left-3.5" : "left-0.5"}`} />
                </button>
                <button
                  onClick={() => toggleExpand(item)}
                  className="text-gray-400 hover:text-gray-700 p-1 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  {expandedId === item.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </button>
              </div>
            </div>
            {expandedId === item.id && <ExpandedForm item={item} />}
          </div>
        ))}
      </div>
    </div>
  );
}

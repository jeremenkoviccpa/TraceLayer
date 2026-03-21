"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Asset } from "@/lib/types";
import { Server, Plus, Trash2, X } from "lucide-react";
import { toast } from "@/lib/toast";

const ASSET_TYPES = ["hardware", "software", "cloud", "data", "other"] as const;
const ENVIRONMENTS = ["production", "staging", "development", "other"] as const;
const CLASSIFICATIONS = ["public", "internal", "confidential", "restricted"] as const;
const STATUSES = ["active", "retired", "disposed"] as const;

const CLASS_STYLES: Record<string, string> = {
  public:       "bg-gray-100 text-gray-600",
  internal:     "bg-blue-50 text-blue-700",
  confidential: "bg-amber-100 text-amber-700",
  restricted:   "bg-red-100 text-red-700",
};

const ENV_STYLES: Record<string, string> = {
  production:  "bg-emerald-50 text-emerald-700",
  staging:     "bg-amber-50 text-amber-700",
  development: "bg-blue-50 text-blue-600",
  other:       "bg-gray-100 text-gray-500",
};

const STATUS_STYLES: Record<string, string> = {
  active:   "bg-emerald-50 text-emerald-700",
  retired:  "bg-gray-100 text-gray-500",
  disposed: "bg-red-50 text-red-500",
};

const TYPE_ICONS: Record<string, string> = {
  hardware: "🖥️", software: "💿", cloud: "☁️", data: "🗄️", other: "📦",
};

const EMPTY: Partial<Asset> = {
  name: "", asset_type: "other", environment: "production", classification: "internal",
  status: "active", vendor: "", version: "", ip_address: "", location: "", description: "",
};

export default function AssetsPage() {
  const [assets, setAssets]       = useState<Asset[]>([]);
  const [loading, setLoading]     = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing]     = useState<Asset | null>(null);
  const [form, setForm]           = useState<Partial<Asset>>(EMPTY);
  const [saving, setSaving]       = useState(false);
  const [filter, setFilter]       = useState<string>("all");

  useEffect(() => {
    api.getAssets().then(setAssets).finally(() => setLoading(false));
  }, []);

  const openCreate = () => { setEditing(null); setForm(EMPTY); setShowModal(true); };
  const openEdit   = (a: Asset) => { setEditing(a); setForm(a); setShowModal(true); };
  const closeModal = () => { setShowModal(false); setEditing(null); setForm(EMPTY); };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault(); setSaving(true);
    try {
      if (editing) {
        const updated = await api.updateAsset(editing.id, form);
        setAssets(prev => prev.map(a => a.id === updated.id ? updated : a));
        toast("Asset updated");
      } else {
        const created = await api.createAsset(form);
        setAssets(prev => [created, ...prev]);
        toast("Asset added");
      }
      closeModal();
    } catch { toast("Failed to save asset", "error"); } finally { setSaving(false); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this asset?")) return;
    try {
      await api.deleteAsset(id);
      setAssets(prev => prev.filter(a => a.id !== id));
      toast("Asset deleted");
    } catch { toast("Failed to delete asset", "error"); }
  };

  const filtered = filter === "all" ? assets : assets.filter(a => a.asset_type === filter);
  const counts = ASSET_TYPES.reduce((acc, t) => ({ ...acc, [t]: assets.filter(a => a.asset_type === t).length }), {} as Record<string, number>);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2.5">
            <Server className="w-6 h-6 text-brand-600" /> Asset Inventory
          </h1>
          <p className="text-sm text-gray-500 mt-1">Track hardware, software, cloud, and data assets</p>
        </div>
        <button onClick={openCreate} className="btn-primary gap-2">
          <Plus className="w-4 h-4" /> Add Asset
        </button>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 flex-wrap">
        {["all", ...ASSET_TYPES].map(t => (
          <button key={t} onClick={() => setFilter(t)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${filter === t ? "bg-brand-600 text-white" : "bg-white border border-gray-200 text-gray-600 hover:border-gray-300"}`}>
            {t === "all" ? `All (${assets.length})` : `${TYPE_ICONS[t]} ${t} (${counts[t] ?? 0})`}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" /></div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-2xl border border-gray-100">
          <Server className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 font-medium">No assets found</p>
          <button onClick={openCreate} className="btn-primary mt-4 gap-2"><Plus className="w-4 h-4" /> Add Asset</button>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Asset</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide hidden md:table-cell">Type</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide hidden sm:table-cell">Environment</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Classification</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide hidden lg:table-cell">Status</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {filtered.map(asset => (
                <tr key={asset.id} className="hover:bg-gray-50/50 transition-colors">
                  <td className="px-4 py-3">
                    <p className="font-medium text-gray-900">{asset.name}</p>
                    {asset.vendor && <p className="text-xs text-gray-400">{asset.vendor}{asset.version ? ` v${asset.version}` : ""}</p>}
                  </td>
                  <td className="px-4 py-3 hidden md:table-cell">
                    <span className="text-sm">{TYPE_ICONS[asset.asset_type]} {asset.asset_type}</span>
                  </td>
                  <td className="px-4 py-3 hidden sm:table-cell">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${ENV_STYLES[asset.environment]}`}>
                      {asset.environment}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${CLASS_STYLES[asset.classification]}`}>
                      {asset.classification}
                    </span>
                  </td>
                  <td className="px-4 py-3 hidden lg:table-cell">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[asset.status]}`}>
                      {asset.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center gap-1 justify-end">
                      <button onClick={() => openEdit(asset)} className="text-xs text-gray-500 hover:text-gray-900 px-2 py-1 rounded hover:bg-gray-100 transition-colors">Edit</button>
                      <button onClick={() => handleDelete(asset.id)} className="text-xs text-red-400 hover:text-red-600 px-2 py-1 rounded hover:bg-red-50 transition-colors"><Trash2 className="w-3.5 h-3.5" /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-900">{editing ? "Edit Asset" : "Add Asset"}</h2>
              <button onClick={closeModal} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
            </div>
            <form onSubmit={handleSave} className="px-6 py-5 space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Name *</label>
                <input className="input" value={form.name ?? ""} onChange={e => setForm(p => ({ ...p, name: e.target.value }))} required placeholder="e.g. Production API Server" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Type</label>
                  <select className="input" value={form.asset_type ?? "other"} onChange={e => setForm(p => ({ ...p, asset_type: e.target.value as Asset["asset_type"] }))}>
                    {ASSET_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Status</label>
                  <select className="input" value={form.status ?? "active"} onChange={e => setForm(p => ({ ...p, status: e.target.value as Asset["status"] }))}>
                    {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Environment</label>
                  <select className="input" value={form.environment ?? "production"} onChange={e => setForm(p => ({ ...p, environment: e.target.value as Asset["environment"] }))}>
                    {ENVIRONMENTS.map(e => <option key={e} value={e}>{e}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Classification</label>
                  <select className="input" value={form.classification ?? "internal"} onChange={e => setForm(p => ({ ...p, classification: e.target.value as Asset["classification"] }))}>
                    {CLASSIFICATIONS.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Vendor</label>
                  <input className="input" value={form.vendor ?? ""} onChange={e => setForm(p => ({ ...p, vendor: e.target.value }))} placeholder="e.g. AWS" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Version</label>
                  <input className="input" value={form.version ?? ""} onChange={e => setForm(p => ({ ...p, version: e.target.value }))} placeholder="e.g. 2.1.4" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">IP Address</label>
                  <input className="input" value={form.ip_address ?? ""} onChange={e => setForm(p => ({ ...p, ip_address: e.target.value }))} />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Location</label>
                  <input className="input" value={form.location ?? ""} onChange={e => setForm(p => ({ ...p, location: e.target.value }))} placeholder="e.g. us-east-1" />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Description</label>
                <textarea className="input min-h-[60px]" value={form.description ?? ""} onChange={e => setForm(p => ({ ...p, description: e.target.value }))} />
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={closeModal} className="btn-secondary flex-1">Cancel</button>
                <button type="submit" disabled={saving} className="btn-primary flex-1 justify-center">
                  {saving ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : editing ? "Save changes" : "Add asset"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

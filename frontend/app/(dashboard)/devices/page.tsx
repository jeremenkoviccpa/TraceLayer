"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Monitor, Plus, Trash2, X, Check, Pencil } from "lucide-react";
import { toast } from "@/lib/toast";

const OS_BADGE: Record<string, string> = {
  mac: "bg-purple-100 text-purple-700",
  windows: "bg-blue-100 text-blue-700",
  linux: "bg-orange-100 text-orange-700",
  other: "bg-gray-100 text-gray-600",
};

const MDM_PLATFORMS = ["Jamf", "Kandji", "Intune", "Other"];

function BoolCheck({ value }: { value: boolean }) {
  return value
    ? <Check className="w-4 h-4 text-emerald-500" />
    : <X className="w-4 h-4 text-red-400" />;
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    compliant: "bg-emerald-50 text-emerald-700",
    non_compliant: "bg-red-50 text-red-700",
    unknown: "bg-gray-100 text-gray-500",
  };
  const labels: Record<string, string> = {
    compliant: "Compliant",
    non_compliant: "Non-compliant",
    unknown: "Unknown",
  };
  return (
    <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${styles[status] ?? styles.unknown}`}>
      {labels[status] ?? status}
    </span>
  );
}

interface DeviceForm {
  employee_email: string;
  employee_name: string;
  hostname: string;
  serial_number: string;
  os_type: string;
  os_version: string;
  disk_encryption: boolean;
  screen_lock: boolean;
  mdm_enrolled: boolean;
  mdm_platform: string;
  notes: string;
}

const emptyForm = (): DeviceForm => ({
  employee_email: "",
  employee_name: "",
  hostname: "",
  serial_number: "",
  os_type: "mac",
  os_version: "",
  disk_encryption: false,
  screen_lock: false,
  mdm_enrolled: false,
  mdm_platform: "",
  notes: "",
});

function DeviceModal({
  initial,
  onClose,
  onSave,
}: {
  initial?: any;
  onClose: () => void;
  onSave: (data: any) => Promise<void>;
}) {
  const [form, setForm] = useState<DeviceForm>(
    initial
      ? {
          employee_email: initial.employee_email ?? "",
          employee_name: initial.employee_name ?? "",
          hostname: initial.hostname ?? "",
          serial_number: initial.serial_number ?? "",
          os_type: initial.os_type ?? "mac",
          os_version: initial.os_version ?? "",
          disk_encryption: initial.disk_encryption ?? false,
          screen_lock: initial.screen_lock ?? false,
          mdm_enrolled: initial.mdm_enrolled ?? false,
          mdm_platform: initial.mdm_platform ?? "",
          notes: initial.notes ?? "",
        }
      : emptyForm()
  );
  const [saving, setSaving] = useState(false);

  const toggle = (key: keyof DeviceForm) =>
    setForm(f => ({ ...f, [key]: !f[key] }));

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave({
        ...form,
        employee_email: form.employee_email || undefined,
        employee_name: form.employee_name || undefined,
        hostname: form.hostname || undefined,
        serial_number: form.serial_number || undefined,
        os_version: form.os_version || undefined,
        mdm_platform: form.mdm_enrolled ? form.mdm_platform || undefined : undefined,
        notes: form.notes || undefined,
      });
      onClose();
    } catch { } finally { setSaving(false); }
  };

  const CheckToggle = ({ label, field }: { label: string; field: keyof DeviceForm }) => (
    <label className="flex items-center gap-2.5 cursor-pointer group">
      <div
        onClick={() => toggle(field)}
        className={`w-5 h-5 rounded-md border-2 flex items-center justify-center shrink-0 transition-all ${
          form[field] ? "bg-emerald-500 border-emerald-500" : "border-gray-300 group-hover:border-emerald-300"
        }`}
      >
        {form[field] && <Check className="w-3 h-3 text-white" />}
      </div>
      <span className="text-sm font-medium text-gray-700">{label}</span>
    </label>
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 space-y-4 my-4">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-gray-900">{initial ? "Edit Device" : "Add Device"}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X className="w-4 h-4" /></button>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Employee email</label>
            <input value={form.employee_email} onChange={e => setForm(f => ({ ...f, employee_email: e.target.value }))} placeholder="alice@company.com" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/30" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Employee name</label>
            <input value={form.employee_name} onChange={e => setForm(f => ({ ...f, employee_name: e.target.value }))} placeholder="Alice Johnson" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/30" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Hostname</label>
            <input value={form.hostname} onChange={e => setForm(f => ({ ...f, hostname: e.target.value }))} placeholder="alice-mbp.local" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/30" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Serial number</label>
            <input value={form.serial_number} onChange={e => setForm(f => ({ ...f, serial_number: e.target.value }))} placeholder="Optional" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/30" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">OS type</label>
            <select value={form.os_type} onChange={e => setForm(f => ({ ...f, os_type: e.target.value }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/30">
              <option value="mac">Mac</option>
              <option value="windows">Windows</option>
              <option value="linux">Linux</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">OS version</label>
            <input value={form.os_version} onChange={e => setForm(f => ({ ...f, os_version: e.target.value }))} placeholder="e.g. 14.4" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/30" />
          </div>
        </div>

        <div className="bg-gray-50 rounded-xl p-4 space-y-3">
          <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide">Security controls</p>
          <CheckToggle label="Disk encryption" field="disk_encryption" />
          <CheckToggle label="Screen lock" field="screen_lock" />
          <CheckToggle label="MDM enrolled" field="mdm_enrolled" />
          {form.mdm_enrolled && (
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">MDM platform</label>
              <select value={form.mdm_platform} onChange={e => setForm(f => ({ ...f, mdm_platform: e.target.value }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/30">
                <option value="">Select platform</option>
                {MDM_PLATFORMS.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
          )}
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-600 mb-1">Notes</label>
          <textarea value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} rows={2} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500/30" />
        </div>

        <div className="flex gap-2 pt-1">
          <button onClick={onClose} className="flex-1 border border-gray-200 rounded-xl py-2 text-sm text-gray-600 hover:bg-gray-50">Cancel</button>
          <button onClick={handleSave} disabled={saving} className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl py-2 text-sm font-semibold disabled:opacity-50">
            {saving ? "Saving…" : initial ? "Save changes" : "Add Device"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function DevicesPage() {
  const [devices, setDevices] = useState<any[]>([]);
  const [stats, setStats] = useState<any>({ total: 0, compliant: 0, non_compliant: 0, unknown: 0, compliance_pct: 0 });
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [editing, setEditing] = useState<any | null>(null);

  const load = async () => {
    try {
      const [d, s] = await Promise.all([api.getDevicesV2(), api.getDeviceStatsV2()]);
      setDevices(d);
      setStats(s);
    } catch { } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (data: any) => {
    const created = await api.createDeviceV2(data);
    setDevices(prev => [created, ...prev]);
    setStats((s: any) => ({ ...s, total: s.total + 1, [created.status]: (s[created.status] ?? 0) + 1, compliance_pct: Math.round(((created.status === "compliant" ? s.compliant + 1 : s.compliant) / (s.total + 1)) * 100) }));
    toast("Device added");
  };

  const handleUpdate = async (data: any) => {
    if (!editing) return;
    const updated = await api.updateDeviceV2(editing.id, data);
    setDevices(prev => prev.map(d => d.id === updated.id ? updated : d));
    setEditing(null);
    toast("Device updated");
  };

  const handleDelete = async (id: string) => {
    try {
      await api.deleteDeviceV2(id);
      setDevices(prev => prev.filter(d => d.id !== id));
      toast("Device removed");
      load(); // refresh stats
    } catch { toast("Failed to delete", "error"); }
  };

  return (
    <div className="animate-fade-in space-y-6">
      {/* Hero */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6 shadow-xl">
        <div className="pointer-events-none absolute inset-0 opacity-[0.03]" style={{ backgroundImage: "linear-gradient(rgba(255,255,255,0.4) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.4) 1px,transparent 1px)", backgroundSize: "24px 24px" }} />
        <div className="relative flex items-start justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/20 ring-1 ring-emerald-500/30">
              <Monitor className="h-5 w-5 text-emerald-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white leading-tight">Devices & Endpoints</h1>
              <p className="text-sm text-slate-400">SOC 2 CC6.7 — track endpoint security across your team's devices.</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex flex-col items-center">
              <span className="text-2xl font-black text-white">{stats.total}</span>
              <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">Total</span>
            </div>
            <div className="w-px h-8 bg-slate-700" />
            <div className="flex flex-col items-center">
              <span className="text-2xl font-black text-emerald-400">{stats.compliant}</span>
              <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">Compliant</span>
            </div>
            <div className="w-px h-8 bg-slate-700" />
            <div className="flex flex-col items-center">
              <span className="text-2xl font-black text-red-400">{stats.non_compliant}</span>
              <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">Non-compliant</span>
            </div>
            <div className="w-px h-8 bg-slate-700" />
            <div className="flex flex-col items-center">
              <span className="text-2xl font-black text-emerald-400">{stats.compliance_pct}%</span>
              <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">Compliant</span>
            </div>
            <button
              onClick={() => setShowAdd(true)}
              className="flex items-center gap-1.5 bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-semibold px-4 py-2 rounded-xl transition-colors"
            >
              <Plus className="w-4 h-4" /> Add Device
            </button>
          </div>
        </div>

        {/* Compliance bar */}
        {stats.total > 0 && (
          <div className="relative mt-5">
            <div className="flex items-center gap-3">
              <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-500 rounded-full transition-all"
                  style={{ width: `${stats.compliance_pct}%` }}
                />
              </div>
              <span className="text-sm font-bold text-emerald-400 shrink-0">{stats.compliance_pct}% compliant</span>
            </div>
          </div>
        )}
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex h-40 items-center justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent" />
        </div>
      ) : devices.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-48 gap-3 rounded-2xl border border-dashed border-gray-200 bg-white text-center">
          <Monitor className="w-8 h-8 text-gray-200" />
          <p className="text-sm font-medium text-gray-500">No devices tracked yet</p>
          <p className="text-xs text-gray-400">Add devices to track endpoint security across your team.</p>
          <button onClick={() => setShowAdd(true)} className="text-xs font-semibold text-emerald-600 hover:text-emerald-700">+ Add first device</button>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50/60">
                <th className="text-left px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-gray-400">Device</th>
                <th className="text-left px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-gray-400 hidden sm:table-cell">OS</th>
                <th className="text-center px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-gray-400">Disk Enc.</th>
                <th className="text-center px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-gray-400">Screen Lock</th>
                <th className="text-left px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-gray-400 hidden md:table-cell">MDM</th>
                <th className="text-left px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-gray-400">Status</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {devices.map(device => (
                <tr key={device.id} className="border-b border-gray-50 hover:bg-gray-50/40 transition-colors">
                  <td className="px-4 py-3">
                    <p className="font-semibold text-gray-800">{device.hostname || device.employee_name || "—"}</p>
                    <p className="text-xs text-gray-400">{device.employee_email || ""}</p>
                  </td>
                  <td className="px-4 py-3 hidden sm:table-cell">
                    <div className="flex items-center gap-2">
                      <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${OS_BADGE[device.os_type ?? "other"] ?? OS_BADGE.other}`}>
                        {device.os_type ?? "—"}
                      </span>
                      {device.os_version && <span className="text-xs text-gray-400">{device.os_version}</span>}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <div className="flex justify-center"><BoolCheck value={device.disk_encryption} /></div>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <div className="flex justify-center"><BoolCheck value={device.screen_lock} /></div>
                  </td>
                  <td className="px-4 py-3 hidden md:table-cell">
                    <div className="flex items-center gap-1.5">
                      <BoolCheck value={device.mdm_enrolled} />
                      {device.mdm_enrolled && device.mdm_platform && (
                        <span className="text-xs text-gray-500">{device.mdm_platform}</span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={device.status} />
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1">
                      <button onClick={() => setEditing(device)} className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors">
                        <Pencil className="w-3.5 h-3.5" />
                      </button>
                      <button onClick={() => handleDelete(device.id)} className="p-1.5 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showAdd && <DeviceModal onClose={() => setShowAdd(false)} onSave={handleCreate} />}
      {editing && <DeviceModal initial={editing} onClose={() => setEditing(null)} onSave={handleUpdate} />}
    </div>
  );
}

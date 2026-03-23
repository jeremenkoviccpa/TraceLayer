"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Device } from "@/lib/types";
import {
  Monitor, Plus, Trash2, Check, X, Shield, ShieldAlert,
  Laptop, Smartphone, Lock, HardDrive, Zap, RefreshCw,
  ChevronDown, ChevronUp, Info,
} from "lucide-react";
import { showToast } from "@/components/ui/Toaster";

const OS_ICONS: Record<string, string> = {
  macos: "🍎", windows: "🪟", linux: "🐧", ios: "📱", android: "🤖", other: "💻",
};

const DEVICE_TYPES = ["laptop", "desktop", "mobile", "tablet", "server", "other"];
const OS_TYPES = ["macos", "windows", "linux", "ios", "android", "other"];

function ComplianceBar({ score }: { score: number }) {
  const color = score === 100 ? "bg-emerald-500" : score >= 67 ? "bg-amber-400" : "bg-red-400";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${score}%` }} />
      </div>
      <span className={`text-xs font-bold w-8 text-right ${score === 100 ? "text-emerald-600" : score >= 67 ? "text-amber-600" : "text-red-500"}`}>
        {score}%
      </span>
    </div>
  );
}

function AttestModal({ onClose, onSave }: {
  onClose: () => void;
  onSave: (d: Device) => void;
}) {
  const [form, setForm] = useState({
    device_name: "",
    device_type: "laptop",
    os_type: "macos",
    os_version: "",
    serial_number: "",
    disk_encrypted: false,
    lockscreen_enabled: false,
    antivirus_installed: false,
  });
  const [saving, setSaving] = useState(false);

  const submit = async () => {
    if (!form.device_name.trim()) { showToast("Device name is required", "error"); return; }
    setSaving(true);
    try {
      const d = await api.attestDevice({
        ...form,
        os_version: form.os_version || undefined,
        serial_number: form.serial_number || undefined,
      });
      onSave(d);
      showToast("Device attestation saved");
      onClose();
    } catch (e: unknown) {
      showToast(e instanceof Error ? e.message : "Failed to save", "error");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl border border-gray-100 shadow-2xl w-full max-w-lg">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-teal-100 flex items-center justify-center">
              <Monitor className="w-4 h-4 text-teal-600" />
            </div>
            <div>
              <p className="font-semibold text-gray-900">Attest My Device</p>
              <p className="text-xs text-gray-400">Confirm your device security controls</p>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-100 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="px-6 py-5 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">Device name *</label>
              <input
                value={form.device_name}
                onChange={e => setForm(f => ({ ...f, device_name: e.target.value }))}
                placeholder="e.g. John's MacBook Pro"
                className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-400"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">Serial number</label>
              <input
                value={form.serial_number}
                onChange={e => setForm(f => ({ ...f, serial_number: e.target.value }))}
                placeholder="Optional"
                className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-400"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">Device type</label>
              <select
                value={form.device_type}
                onChange={e => setForm(f => ({ ...f, device_type: e.target.value }))}
                className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30"
              >
                {DEVICE_TYPES.map(t => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">Operating system</label>
              <select
                value={form.os_type}
                onChange={e => setForm(f => ({ ...f, os_type: e.target.value }))}
                className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30"
              >
                {OS_TYPES.map(t => <option key={t} value={t}>{OS_ICONS[t]} {t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1.5">OS version</label>
            <input
              value={form.os_version}
              onChange={e => setForm(f => ({ ...f, os_version: e.target.value }))}
              placeholder="e.g. 14.4"
              className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-400"
            />
          </div>

          <div className="bg-gray-50 rounded-xl p-4 space-y-3">
            <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide">Security controls</p>
            {[
              { key: "disk_encrypted", label: "Disk encryption enabled", icon: HardDrive, desc: "FileVault, BitLocker, or equivalent" },
              { key: "lockscreen_enabled", label: "Lockscreen / auto-lock enabled", icon: Lock, desc: "Screen locks after inactivity" },
              { key: "antivirus_installed", label: "Antivirus / EDR installed", icon: Shield, desc: "Real-time protection software" },
            ].map(({ key, label, icon: Icon, desc }) => (
              <label key={key} className="flex items-center gap-3 cursor-pointer group">
                <div
                  onClick={() => setForm(f => ({ ...f, [key]: !f[key as keyof typeof form] }))}
                  className={`w-5 h-5 rounded-md border-2 flex items-center justify-center shrink-0 transition-all ${form[key as keyof typeof form] ? "bg-teal-500 border-teal-500" : "border-gray-300 group-hover:border-teal-300"}`}
                >
                  {form[key as keyof typeof form] && <Check className="w-3 h-3 text-white" />}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <Icon className="w-3.5 h-3.5 text-gray-400" />
                    <span className="text-sm font-medium text-gray-700">{label}</span>
                  </div>
                  <p className="text-xs text-gray-400 mt-0.5">{desc}</p>
                </div>
              </label>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-100">
          <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-xl transition-colors">
            Cancel
          </button>
          <button
            onClick={submit}
            disabled={saving}
            className="flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold px-5 py-2 rounded-xl text-sm transition-colors disabled:opacity-50"
          >
            {saving ? <><span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />Saving…</> : <><Check className="w-3.5 h-3.5" />Attest device</>}
          </button>
        </div>
      </div>
    </div>
  );
}

function AddDeviceModal({ onClose, onSave }: {
  onClose: () => void;
  onSave: (d: Device) => void;
}) {
  const [form, setForm] = useState({
    device_name: "",
    device_type: "laptop",
    os_type: "macos",
    os_version: "",
    serial_number: "",
    notes: "",
  });
  const [saving, setSaving] = useState(false);

  const submit = async () => {
    if (!form.device_name.trim()) { showToast("Device name is required", "error"); return; }
    setSaving(true);
    try {
      const d = await api.createDevice({
        device_name: form.device_name,
        device_type: form.device_type,
        os_type: form.os_type,
        os_version: form.os_version || undefined,
        serial_number: form.serial_number || undefined,
        notes: form.notes || undefined,
      } as Partial<Device>);
      onSave(d);
      showToast("Device added");
      onClose();
    } catch (e: unknown) {
      showToast(e instanceof Error ? e.message : "Failed to add device", "error");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl border border-gray-100 shadow-2xl w-full max-w-lg">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <p className="font-semibold text-gray-900">Add Device</p>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-100 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="px-6 py-5 space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1.5">Device name *</label>
            <input
              value={form.device_name}
              onChange={e => setForm(f => ({ ...f, device_name: e.target.value }))}
              placeholder="e.g. Alice's ThinkPad"
              className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-400"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">Device type</label>
              <select value={form.device_type} onChange={e => setForm(f => ({ ...f, device_type: e.target.value }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none">
                {DEVICE_TYPES.map(t => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">OS</label>
              <select value={form.os_type} onChange={e => setForm(f => ({ ...f, os_type: e.target.value }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none">
                {OS_TYPES.map(t => <option key={t} value={t}>{OS_ICONS[t]} {t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">OS version</label>
              <input value={form.os_version} onChange={e => setForm(f => ({ ...f, os_version: e.target.value }))} placeholder="e.g. 11.0" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">Serial number</label>
              <input value={form.serial_number} onChange={e => setForm(f => ({ ...f, serial_number: e.target.value }))} placeholder="Optional" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1.5">Notes</label>
            <textarea value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} rows={2} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30 resize-none" />
          </div>
        </div>
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-100">
          <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-xl transition-colors">Cancel</button>
          <button onClick={submit} disabled={saving} className="flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold px-5 py-2 rounded-xl text-sm transition-colors disabled:opacity-50">
            {saving ? "Adding…" : <><Plus className="w-3.5 h-3.5" />Add device</>}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function DevicesPage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAttest, setShowAttest] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  const load = async () => {
    try {
      const d = await api.getDevices();
      setDevices(d);
    } catch {
      // admin only — non-admins see empty
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleDelete = async (id: string) => {
    setDeleting(id);
    try {
      await api.deleteDevice(id);
      setDevices(prev => prev.filter(d => d.id !== id));
      showToast("Device removed");
    } catch (e: unknown) {
      showToast(e instanceof Error ? e.message : "Failed to delete", "error");
    } finally {
      setDeleting(null);
    }
  };

  const totalDevices = devices.length;
  const compliantCount = devices.filter(d => d.is_compliant).length;
  const needsAttestCount = devices.filter(d => !d.last_attested_at).length;
  const avgScore = totalDevices ? Math.round(devices.reduce((s, d) => s + d.compliance_score, 0) / totalDevices) : 0;

  return (
    <div className="space-y-6">
      {/* Hero */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl p-6 shadow-xl">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="flex items-start gap-4">
            <div className="w-11 h-11 rounded-xl bg-teal-500/20 flex items-center justify-center shrink-0">
              <Monitor className="w-5 h-5 text-teal-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Device Monitoring</h1>
              <p className="text-sm text-slate-400 mt-0.5">Track employee device security controls — disk encryption, lockscreen, and antivirus compliance.</p>
              <div className="flex flex-wrap gap-6 mt-4">
                <div>
                  <p className="text-2xl font-bold text-white">{totalDevices}</p>
                  <p className="text-xs text-slate-500 mt-0.5">Total devices</p>
                </div>
                <div className="hidden sm:block w-px h-8 bg-slate-700 self-center" />
                <div>
                  <p className="text-2xl font-bold text-emerald-400">{compliantCount}</p>
                  <p className="text-xs text-slate-500 mt-0.5">Fully compliant</p>
                </div>
                <div className="hidden sm:block w-px h-8 bg-slate-700 self-center" />
                <div>
                  <p className="text-2xl font-bold text-amber-400">{needsAttestCount}</p>
                  <p className="text-xs text-slate-500 mt-0.5">Not yet attested</p>
                </div>
                <div className="hidden sm:block w-px h-8 bg-slate-700 self-center" />
                <div>
                  <p className="text-2xl font-bold text-teal-400">{avgScore}%</p>
                  <p className="text-xs text-slate-500 mt-0.5">Avg compliance</p>
                </div>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => setShowAttest(true)}
              className="flex items-center gap-2 bg-teal-600 hover:bg-teal-500 text-white font-semibold px-4 py-2 rounded-xl text-sm transition-colors"
            >
              <Shield className="w-4 h-4" />
              Attest my device
            </button>
            <button
              onClick={() => setShowAdd(true)}
              className="flex items-center gap-2 bg-white/10 hover:bg-white/20 text-white font-semibold px-4 py-2 rounded-xl text-sm transition-colors"
            >
              <Plus className="w-4 h-4" />
              Add device
            </button>
          </div>
        </div>
      </div>

      {/* SOC 2 context */}
      <div className="bg-blue-50 border border-blue-100 rounded-xl px-4 py-3 flex items-start gap-3">
        <Info className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
        <p className="text-sm text-blue-700">
          SOC 2 requires evidence that employee devices meet your security policy. Collect attestations from all employees with access to production systems — auditors will ask for a full device inventory.
        </p>
      </div>

      {/* Device list */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <p className="font-semibold text-gray-800">All Devices ({totalDevices})</p>
          <button onClick={load} className="text-gray-400 hover:text-gray-600 p-1.5 rounded-lg hover:bg-gray-100 transition-colors">
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="w-6 h-6 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : devices.length === 0 ? (
          <div className="text-center py-16">
            <Monitor className="w-12 h-12 text-gray-200 mx-auto mb-3" />
            <p className="font-semibold text-gray-400">No devices yet</p>
            <p className="text-sm text-gray-300 mt-1 mb-4">Add devices manually or ask employees to self-attest</p>
            <div className="flex items-center justify-center gap-3">
              <button onClick={() => setShowAttest(true)} className="flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold px-4 py-2 rounded-xl text-sm transition-colors">
                <Shield className="w-4 h-4" />Attest my device
              </button>
              <button onClick={() => setShowAdd(true)} className="flex items-center gap-2 border border-gray-200 text-gray-600 hover:bg-gray-50 font-semibold px-4 py-2 rounded-xl text-sm transition-colors">
                <Plus className="w-4 h-4" />Add device
              </button>
            </div>
          </div>
        ) : (
          <div className="divide-y divide-gray-50">
            {devices.map(device => {
              const isOpen = expanded === device.id;
              const scoreColor = device.compliance_score === 100 ? "text-emerald-600" : device.compliance_score >= 67 ? "text-amber-600" : "text-red-500";
              const Icon = device.compliance_score === 100 ? Shield : ShieldAlert;
              const iconColor = device.compliance_score === 100 ? "text-emerald-500" : device.compliance_score >= 67 ? "text-amber-500" : "text-red-400";

              return (
                <div key={device.id}>
                  <button
                    className="w-full flex items-center gap-4 px-6 py-4 hover:bg-gray-50 transition-colors text-left"
                    onClick={() => setExpanded(isOpen ? null : device.id)}
                  >
                    <div className="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center shrink-0 text-lg">
                      {OS_ICONS[device.os_type] || "💻"}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="font-semibold text-gray-800 text-sm truncate">{device.device_name}</p>
                        <span className="text-[10px] font-medium text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full shrink-0">
                          {device.device_type} · {device.os_type}
                        </span>
                        {!device.last_attested_at && (
                          <span className="text-[10px] font-semibold text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full shrink-0">
                            Not attested
                          </span>
                        )}
                      </div>
                      <div className="w-32">
                        <ComplianceBar score={device.compliance_score} />
                      </div>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <Icon className={`w-4 h-4 ${iconColor}`} />
                      {isOpen ? <ChevronUp className="w-4 h-4 text-gray-300" /> : <ChevronDown className="w-4 h-4 text-gray-300" />}
                    </div>
                  </button>

                  {isOpen && (
                    <div className="bg-gray-50 border-t border-gray-100 px-6 py-5">
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-5">
                        {[
                          { label: "Disk encryption", ok: device.disk_encrypted, icon: HardDrive },
                          { label: "Lockscreen", ok: device.lockscreen_enabled, icon: Lock },
                          { label: "Antivirus / EDR", ok: device.antivirus_installed, icon: Shield },
                        ].map(({ label, ok, icon: Icon }) => (
                          <div key={label} className={`flex items-center gap-2.5 rounded-xl border px-3 py-2.5 ${ok ? "border-emerald-200 bg-emerald-50" : "border-red-100 bg-red-50"}`}>
                            <Icon className={`w-3.5 h-3.5 shrink-0 ${ok ? "text-emerald-500" : "text-red-400"}`} />
                            <div>
                              <p className="text-xs font-medium text-gray-700">{label}</p>
                              <p className={`text-[10px] font-semibold ${ok ? "text-emerald-600" : "text-red-500"}`}>
                                {ok ? "✓ Enabled" : "✗ Not confirmed"}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>

                      <div className="flex items-center justify-between flex-wrap gap-2 text-xs text-gray-400">
                        <div className="flex items-center gap-4">
                          {device.attested_by_email && (
                            <span>Attested by: <span className="text-gray-600">{device.attested_by_email}</span></span>
                          )}
                          {device.last_attested_at && (
                            <span>Last attested: <span className="text-gray-600">{new Date(device.last_attested_at).toLocaleDateString()}</span></span>
                          )}
                          {device.serial_number && (
                            <span>S/N: <span className="text-gray-600">{device.serial_number}</span></span>
                          )}
                        </div>
                        <button
                          onClick={() => handleDelete(device.id)}
                          disabled={deleting === device.id}
                          className="flex items-center gap-1 text-red-400 hover:text-red-600 hover:bg-red-50 px-2 py-1 rounded-lg transition-colors disabled:opacity-50"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                          {deleting === device.id ? "Removing…" : "Remove"}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {showAttest && (
        <AttestModal
          onClose={() => setShowAttest(false)}
          onSave={d => setDevices(prev => {
            const idx = prev.findIndex(x => x.user_id === d.user_id);
            if (idx >= 0) {
              const next = [...prev];
              next[idx] = d;
              return next;
            }
            return [d, ...prev];
          })}
        />
      )}

      {showAdd && (
        <AddDeviceModal
          onClose={() => setShowAdd(false)}
          onSave={d => setDevices(prev => [d, ...prev])}
        />
      )}
    </div>
  );
}

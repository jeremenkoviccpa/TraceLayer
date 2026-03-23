"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { DeviceTaskItem, PolicyContentResponse, PolicyTaskItem, PortalTasksResponse } from "@/lib/types";
import {
  CheckCircle2, Clock, FileText, Monitor, AlertTriangle,
  ChevronDown, ChevronUp, X, Loader2,
} from "lucide-react";
import { showToast } from "@/components/ui/Toaster";

// ── Policy Sign Modal ─────────────────────────────────────────────────────────

function PolicyModal({
  slug,
  onClose,
  onSigned,
}: {
  slug: string;
  onClose: () => void;
  onSigned: (item: PolicyTaskItem) => void;
}) {
  const [policy, setPolicy] = useState<PolicyContentResponse | null>(null);
  const [agreed, setAgreed] = useState(false);
  const [signing, setSigning] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.getPortalPolicy(slug).then(setPolicy).catch(() => onClose());
  }, [slug, onClose]);

  const sign = async () => {
    setSigning(true);
    try {
      const updated = await api.signPolicy(slug);
      onSigned(updated);
      showToast("Policy signed successfully");
      onClose();
    } catch (e: unknown) {
      showToast(e instanceof Error ? e.message : "Failed to sign policy", "error");
    } finally {
      setSigning(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-teal-100 flex items-center justify-center">
              <FileText className="w-4 h-4 text-teal-600" />
            </div>
            <div>
              <p className="text-sm font-bold text-gray-900">{policy?.title ?? "Loading…"}</p>
              <p className="text-xs text-gray-400">Read the full policy before signing</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors">
            <X className="w-4 h-4 text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div ref={contentRef} className="flex-1 overflow-y-auto px-6 py-4">
          {!policy ? (
            <div className="flex items-center justify-center h-32">
              <Loader2 className="w-6 h-6 text-teal-500 animate-spin" />
            </div>
          ) : (
            <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap leading-relaxed text-sm">
              {policy.content}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-100 space-y-3 shrink-0">
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={agreed}
              onChange={e => setAgreed(e.target.checked)}
              className="mt-0.5 w-4 h-4 rounded border-gray-300 text-teal-600 focus:ring-teal-500"
            />
            <span className="text-sm text-gray-600 leading-snug">
              I have read and understand the <strong>{policy?.title}</strong> and agree to comply with its terms.
            </span>
          </label>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 py-2.5 rounded-xl border border-gray-200 text-sm font-semibold text-gray-600 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={sign}
              disabled={!agreed || signing || !policy}
              className="flex-1 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-500 text-white text-sm font-semibold transition-colors disabled:opacity-40 flex items-center justify-center gap-2"
            >
              {signing ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
              {signing ? "Signing…" : "Sign policy"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Device Attest Inline ──────────────────────────────────────────────────────

function DeviceAttestCard({ device, onAttested }: { device: DeviceTaskItem; onAttested: () => void }) {
  const [form, setForm] = useState({
    device_name: "",
    device_type: "laptop",
    os_type: "macos",
    disk_encrypted: false,
    lockscreen_enabled: false,
    antivirus_installed: false,
  });
  const [saving, setSaving] = useState(false);

  const attest = async () => {
    if (!form.device_name.trim()) { showToast("Enter a device name", "error"); return; }
    setSaving(true);
    try {
      await api.attestDevice(form);
      showToast("Device attested successfully");
      onAttested();
    } catch (e: unknown) {
      showToast(e instanceof Error ? e.message : "Failed to attest device", "error");
    } finally {
      setSaving(false);
    }
  };

  if (device.attested) {
    const score = [device.disk_encrypted, device.lockscreen_enabled, device.antivirus_installed].filter(Boolean).length;
    return (
      <div className="flex items-start gap-4">
        <div className="w-9 h-9 rounded-xl bg-emerald-100 flex items-center justify-center shrink-0">
          <CheckCircle2 className="w-5 h-5 text-emerald-600" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-gray-800">{device.device_name}</p>
          <p className="text-xs text-gray-400 mt-0.5">
            Last attested {device.last_attested_at ? new Date(device.last_attested_at).toLocaleDateString() : "recently"} · {score}/3 controls passing
          </p>
          <div className="flex gap-2 mt-2 flex-wrap">
            {[
              { label: "Disk encrypted", val: device.disk_encrypted },
              { label: "Lockscreen", val: device.lockscreen_enabled },
              { label: "Antivirus", val: device.antivirus_installed },
            ].map(({ label, val }) => (
              <span key={label} className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${val ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-600"}`}>
                {val ? "✓" : "✗"} {label}
              </span>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 mb-1">
        <AlertTriangle className="w-4 h-4 text-amber-500" />
        <p className="text-sm font-medium text-amber-700">Your device hasn't been attested yet</p>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="col-span-2">
          <input
            value={form.device_name}
            onChange={e => setForm(f => ({ ...f, device_name: e.target.value }))}
            placeholder="Device name (e.g. MacBook Pro 14)"
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
          />
        </div>
        <select
          value={form.device_type}
          onChange={e => setForm(f => ({ ...f, device_type: e.target.value }))}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
        >
          {["laptop", "desktop", "mobile", "tablet", "server"].map(t => (
            <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
          ))}
        </select>
        <select
          value={form.os_type}
          onChange={e => setForm(f => ({ ...f, os_type: e.target.value }))}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
        >
          {["macos", "windows", "linux", "ios", "android"].map(o => (
            <option key={o} value={o}>{o.charAt(0).toUpperCase() + o.slice(1)}</option>
          ))}
        </select>
      </div>
      <div className="space-y-2">
        {[
          { key: "disk_encrypted" as const, label: "Disk encryption enabled (FileVault / BitLocker)" },
          { key: "lockscreen_enabled" as const, label: "Lockscreen / auto-lock enabled" },
          { key: "antivirus_installed" as const, label: "Antivirus / endpoint protection installed" },
        ].map(({ key, label }) => (
          <label key={key} className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={form[key]}
              onChange={e => setForm(f => ({ ...f, [key]: e.target.checked }))}
              className="w-4 h-4 rounded border-gray-300 text-teal-600 focus:ring-teal-500"
            />
            <span className="text-sm text-gray-600">{label}</span>
          </label>
        ))}
      </div>
      <button
        onClick={attest}
        disabled={saving}
        className="w-full py-2.5 bg-teal-600 hover:bg-teal-500 text-white text-sm font-semibold rounded-xl transition-colors disabled:opacity-40 flex items-center justify-center gap-2"
      >
        {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Monitor className="w-4 h-4" />}
        {saving ? "Saving…" : "Attest my device"}
      </button>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function PortalPage() {
  const [tasks, setTasks] = useState<PortalTasksResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [signingSlug, setSigningSlug] = useState<string | null>(null);
  const [policiesOpen, setPoliciesOpen] = useState(true);
  const [deviceOpen, setDeviceOpen] = useState(true);

  const load = async () => {
    try {
      const data = await api.getPortalTasks();
      setTasks(data);
    } catch {
      showToast("Failed to load your tasks", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 text-teal-500 animate-spin" />
      </div>
    );
  }

  if (!tasks) return null;

  const { pending_count, total_count, policies, device } = tasks;
  const completed = total_count - pending_count;
  const pct = total_count > 0 ? Math.round((completed / total_count) * 100) : 100;
  const allDone = pending_count === 0;

  const firstName = tasks.user_name?.split(" ")[0] ?? tasks.user_email.split("@")[0];

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 space-y-6">
      {/* Hero */}
      <div className={`rounded-2xl p-6 border ${allDone ? "bg-emerald-50 border-emerald-200" : "bg-white border-gray-100 shadow-sm"}`}>
        <div className="flex items-start justify-between gap-4 mb-4">
          <div>
            <h1 className="text-xl font-extrabold text-gray-900 mb-1">
              Hi {firstName}! {allDone ? "🎉" : "👋"}
            </h1>
            <p className="text-sm text-gray-500">
              {allDone
                ? "You're fully compliant — all tasks complete."
                : `You have ${pending_count} pending compliance ${pending_count === 1 ? "task" : "tasks"}.`}
            </p>
          </div>
          <div className="text-right shrink-0">
            <p className="text-2xl font-black text-teal-600">{pct}%</p>
            <p className="text-xs text-gray-400">{completed}/{total_count} done</p>
          </div>
        </div>
        {/* Progress bar */}
        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${allDone ? "bg-emerald-500" : "bg-teal-500"}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {/* Policy sign-offs */}
      {policies.length > 0 && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          <button
            onClick={() => setPoliciesOpen(o => !o)}
            className="w-full flex items-center justify-between px-5 py-4 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center">
                <FileText className="w-4 h-4 text-blue-600" />
              </div>
              <div className="text-left">
                <p className="text-sm font-bold text-gray-800">Policy Sign-offs</p>
                <p className="text-xs text-gray-400">
                  {policies.filter(p => p.signed).length}/{policies.length} signed
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {policies.some(p => !p.signed) && (
                <span className="text-[10px] font-bold bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">
                  {policies.filter(p => !p.signed).length} pending
                </span>
              )}
              {policiesOpen ? <ChevronUp className="w-4 h-4 text-gray-300" /> : <ChevronDown className="w-4 h-4 text-gray-300" />}
            </div>
          </button>

          {policiesOpen && (
            <div className="border-t border-gray-100 divide-y divide-gray-50">
              {policies.map(p => (
                <div key={p.policy_id} className="flex items-center justify-between px-5 py-3.5">
                  <div className="flex items-center gap-3 min-w-0">
                    {p.signed
                      ? <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                      : <Clock className="w-4 h-4 text-amber-400 shrink-0" />
                    }
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-800 truncate">{p.title}</p>
                      {p.signed && p.signed_at && (
                        <p className="text-xs text-gray-400">Signed {new Date(p.signed_at).toLocaleDateString()}</p>
                      )}
                    </div>
                  </div>
                  {p.signed ? (
                    <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full shrink-0">Signed</span>
                  ) : (
                    <button
                      onClick={() => setSigningSlug(p.slug)}
                      className="shrink-0 text-xs font-semibold bg-teal-600 hover:bg-teal-500 text-white px-3 py-1.5 rounded-lg transition-colors"
                    >
                      Read & Sign
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Device attestation */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <button
          onClick={() => setDeviceOpen(o => !o)}
          className="w-full flex items-center justify-between px-5 py-4 hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-purple-100 flex items-center justify-center">
              <Monitor className="w-4 h-4 text-purple-600" />
            </div>
            <div className="text-left">
              <p className="text-sm font-bold text-gray-800">Device Attestation</p>
              <p className="text-xs text-gray-400">
                {device.attested ? "Device attested" : "Not yet attested"}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {!device.attested && (
              <span className="text-[10px] font-bold bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">Required</span>
            )}
            {deviceOpen ? <ChevronUp className="w-4 h-4 text-gray-300" /> : <ChevronDown className="w-4 h-4 text-gray-300" />}
          </div>
        </button>
        {deviceOpen && (
          <div className="border-t border-gray-100 px-5 py-4">
            <DeviceAttestCard
              device={device}
              onAttested={load}
            />
          </div>
        )}
      </div>

      {/* Training — stub */}
      <div className="bg-white rounded-2xl border border-dashed border-gray-200 px-5 py-4 flex items-center gap-4 opacity-60">
        <div className="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center shrink-0">
          <span className="text-sm">🎓</span>
        </div>
        <div>
          <p className="text-sm font-bold text-gray-700">Security Awareness Training</p>
          <p className="text-xs text-gray-400">Coming soon — modules launching shortly.</p>
        </div>
        <span className="ml-auto text-[10px] font-bold text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full shrink-0">Soon</span>
      </div>

      {/* Policy modal */}
      {signingSlug && (
        <PolicyModal
          slug={signingSlug}
          onClose={() => setSigningSlug(null)}
          onSigned={updated => {
            setTasks(t => t ? {
              ...t,
              policies: t.policies.map(p => p.slug === updated.slug ? updated : p),
              pending_count: t.policies.filter(p => p.slug === updated.slug ? false : !p.signed).length
                + (t.device.attested ? 0 : 1),
            } : t);
          }}
        />
      )}
    </div>
  );
}

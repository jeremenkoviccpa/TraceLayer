"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { BillingInfo, Integration } from "@/lib/types";
import { CheckCircle2, AlertCircle, Clock, RefreshCw, Trash2, Plus, X, Zap, Lock, Search } from "lucide-react";

const FREE_LIMIT = 3;

// ── Brand logo badges (inline SVG, no external images) ────────────────────────
type LogoCfg = { bg: string; label: string; svg?: (s: number) => React.ReactNode };

const LOGO_CONFIG: Record<string, LogoCfg> = {
  aws: {
    bg: "#232F3E", label: "AWS",
    svg: (s) => (
      <>
        <text x={s/2} y={s*0.46} textAnchor="middle" dominantBaseline="central" fill="white" fontFamily="system-ui" fontWeight="800" fontSize={s*0.27}>AWS</text>
        <path d={`M${s*0.27} ${s*0.67} Q${s*0.5} ${s*0.78} ${s*0.73} ${s*0.67}`} stroke="#FF9900" strokeWidth={s*0.07} strokeLinecap="round" fill="none"/>
      </>
    ),
  },
  github: {
    bg: "#24292E", label: "GH",
    svg: (s) => {
      const cx = s/2, cy = s/2, r = s*0.29;
      return (
        <>
          <circle cx={cx} cy={cy} r={r} fill="white"/>
          <circle cx={cx} cy={cy-r*0.07} r={r*0.62} fill="#24292E"/>
          <ellipse cx={cx-r*0.42} cy={cy-r*0.58} rx={r*0.19} ry={r*0.24} fill="white"/>
          <ellipse cx={cx+r*0.42} cy={cy-r*0.58} rx={r*0.19} ry={r*0.24} fill="white"/>
          <circle cx={cx-r*0.23} cy={cy-r*0.08} r={r*0.11} fill="white"/>
          <circle cx={cx+r*0.23} cy={cy-r*0.08} r={r*0.11} fill="white"/>
        </>
      );
    },
  },
  slack: {
    bg: "#4A154B", label: "SK",
    svg: (s) => {
      const c=s/2, r=s*0.13, g=s*0.06;
      return (
        <>
          <rect x={c-r*2-g/2} y={c-r*2-g/2} width={r*2} height={r*2} rx={r*0.5} fill="#E01E5A"/>
          <rect x={c+g/2}     y={c-r*2-g/2} width={r*2} height={r*2} rx={r*0.5} fill="#36C5F0"/>
          <rect x={c-r*2-g/2} y={c+g/2}     width={r*2} height={r*2} rx={r*0.5} fill="#2EB67D"/>
          <rect x={c+g/2}     y={c+g/2}     width={r*2} height={r*2} rx={r*0.5} fill="#ECB22E"/>
        </>
      );
    },
  },
  google_workspace: {
    bg: "#FFFFFF", label: "GW",
    svg: (s) => {
      const cx=s/2, cy=s/2, r=s*0.29;
      const gx=cx+r*0.15;
      return (
        <>
          <rect width={s} height={s} rx={Math.round(s*0.25)} fill="white" stroke="#E5E7EB" strokeWidth="1.5"/>
          <path d={`M${gx} ${cy} L${gx} ${cy-r*0.55} L${cx-r*0.35} ${cy-r*0.55}`} stroke="#4285F4" strokeWidth={s*0.09} strokeLinecap="round" fill="none"/>
          <path d={`M${cx-r} ${cy} A${r} ${r} 0 1 1 ${cx+r*0.7} ${cy+r*0.7}`} stroke="#EA4335" strokeWidth={s*0.09} fill="none" strokeLinecap="round"/>
          <path d={`M${cx+r*0.7} ${cy+r*0.7} A${r} ${r} 0 0 1 ${cx+r} ${cy}`} stroke="#FBBC05" strokeWidth={s*0.09} fill="none" strokeLinecap="round"/>
          <line x1={cx} y1={cy} x2={gx} y2={cy} stroke="#34A853" strokeWidth={s*0.09} strokeLinecap="round"/>
        </>
      );
    },
  },
  okta: {
    bg: "#007DC1", label: "OK",
    svg: (s) => (
      <>
        <circle cx={s/2} cy={s/2} r={s*0.27} stroke="white" strokeWidth={s*0.09} fill="none"/>
        <circle cx={s/2} cy={s/2} r={s*0.09} fill="white"/>
      </>
    ),
  },
  azure_ad: {
    bg: "#0078D4", label: "AD",
    svg: (s) => {
      const cx=s/2, cy=s/2, hw=s*0.14, gap=s*0.05;
      return (
        <>
          <rect x={cx-hw*2-gap/2} y={cy-hw*2-gap/2} width={hw*2} height={hw*2} rx={2} fill="white" opacity={0.95}/>
          <rect x={cx+gap/2}      y={cy-hw*2-gap/2} width={hw*2} height={hw*2} rx={2} fill="white" opacity={0.75}/>
          <rect x={cx-hw*2-gap/2} y={cy+gap/2}      width={hw*2} height={hw*2} rx={2} fill="white" opacity={0.75}/>
          <rect x={cx+gap/2}      y={cy+gap/2}      width={hw*2} height={hw*2} rx={2} fill="white" opacity={0.5}/>
        </>
      );
    },
  },
  jira: {
    bg: "#0052CC", label: "JR",
    svg: (s) => {
      const cx=s/2, cy=s/2, r=s*0.27;
      return (
        <>
          <path d={`M${cx} ${cy-r} L${cx+r} ${cy} L${cx} ${cy} Z`} fill="white" opacity="0.5"/>
          <path d={`M${cx} ${cy} L${cx+r} ${cy} L${cx} ${cy+r} Z`} fill="white"/>
          <path d={`M${cx-r} ${cy} L${cx} ${cy} L${cx} ${cy+r} Z`} fill="white" opacity="0.5"/>
          <path d={`M${cx-r} ${cy} L${cx} ${cy-r} L${cx} ${cy} Z`} fill="white" opacity="0.3"/>
        </>
      );
    },
  },
  gitlab: {
    bg: "#E24329", label: "GL",
    svg: (s) => {
      const cx=s/2, cy=s*0.52, w=s*0.36, h=s*0.28;
      return (
        <>
          <path d={`M${cx} ${cy-h} L${cx+w} ${cy+h} L${cx-w} ${cy+h} Z`} fill="white"/>
          <path d={`M${cx-w} ${cy+h} L${cx-w*1.35} ${cy} L${cx} ${cy-h} Z`} fill="white" opacity="0.6"/>
          <path d={`M${cx+w} ${cy+h} L${cx+w*1.35} ${cy} L${cx} ${cy-h} Z`} fill="white" opacity="0.6"/>
        </>
      );
    },
  },
  google_cloud: {
    bg: "#4285F4", label: "GC",
    svg: (s) => (
      <>
        <text x={s/2} y={s/2} textAnchor="middle" dominantBaseline="central" fill="white" fontFamily="system-ui" fontWeight="800" fontSize={s*0.36}>G</text>
        <circle cx={s*0.69} cy={s*0.31} r={s*0.12} fill="#34A853"/>
      </>
    ),
  },
  linear: {
    bg: "#5E6AD2", label: "LN",
    svg: (s) => {
      const p=s*0.23;
      return (
        <path d={`M${p} ${s-p} L${s-p} ${p} L${s-p} ${s*0.57} M${s*0.43} ${p} L${s-p} ${p}`}
          stroke="white" strokeWidth={s*0.1} strokeLinecap="round" strokeLinejoin="round" fill="none"/>
      );
    },
  },
  datadog: {
    bg: "#632CA6", label: "DD",
    svg: (s) => <text x={s/2} y={s/2} textAnchor="middle" dominantBaseline="central" fill="white" fontFamily="system-ui" fontWeight="800" fontSize={s*0.29}>DD</text>,
  },
  pagerduty: {
    bg: "#06AC38", label: "PD",
    svg: (s) => <text x={s/2} y={s/2} textAnchor="middle" dominantBaseline="central" fill="white" fontFamily="system-ui" fontWeight="800" fontSize={s*0.29}>PD</text>,
  },
  sentry: {
    bg: "#362D59", label: "SN",
    svg: (s) => (
      <path d={`M${s*0.5} ${s*0.72} L${s*0.18} ${s*0.17} L${s*0.82} ${s*0.17} Z`}
        fill="none" stroke="white" strokeWidth={s*0.09} strokeLinejoin="round"/>
    ),
  },
  microsoft_teams: {
    bg: "#5B5EA6", label: "T",
    svg: (s) => <text x={s/2} y={s/2} textAnchor="middle" dominantBaseline="central" fill="white" fontFamily="system-ui" fontWeight="800" fontSize={s*0.4}>T</text>,
  },
  stripe: {
    bg: "#635BFF", label: "S",
    svg: (s) => <text x={s/2} y={s/2} textAnchor="middle" dominantBaseline="central" fill="white" fontFamily="system-ui" fontWeight="800" fontSize={s*0.4}>S</text>,
  },
  rippling: {
    bg: "#E9410E", label: "RP",
    svg: (s) => <text x={s/2} y={s/2} textAnchor="middle" dominantBaseline="central" fill="white" fontFamily="system-ui" fontWeight="800" fontSize={s*0.38}>R</text>,
  },
  bamboohr: {
    bg: "#6AAF3D", label: "BH",
    svg: (s) => <text x={s/2} y={s/2} textAnchor="middle" dominantBaseline="central" fill="white" fontFamily="system-ui" fontWeight="800" fontSize={s*0.29}>BH</text>,
  },
  notion: {
    bg: "#191919", label: "N",
    svg: (s) => <text x={s/2} y={s/2} textAnchor="middle" dominantBaseline="central" fill="white" fontFamily="Georgia,serif" fontWeight="700" fontSize={s*0.44}>N</text>,
  },
};

function LogoBadge({ type, size = 42 }: { type: string; size?: number }) {
  const cfg = LOGO_CONFIG[type] ?? { bg: "#6B7280", label: type.slice(0, 2).toUpperCase() };
  const s = size;
  const r = Math.round(s * 0.25);
  return (
    <svg width={s} height={s} viewBox={`0 0 ${s} ${s}`} fill="none" xmlns="http://www.w3.org/2000/svg" className="shrink-0">
      <rect width={s} height={s} rx={r} fill={cfg.bg}/>
      {cfg.svg ? cfg.svg(s) : (
        <text x={s/2} y={s/2} textAnchor="middle" dominantBaseline="central" fill="white"
          fontFamily="system-ui,-apple-system,sans-serif" fontWeight="700"
          fontSize={cfg.label.length > 2 ? s*0.28 : s*0.35}>
          {cfg.label}
        </text>
      )}
    </svg>
  );
}

// ── Integration definitions ───────────────────────────────────────────────────
type IntegrationDef = {
  type: string;
  label: string;
  description: string;
  comingSoon?: boolean;
  fields?: { key: string; label: string; placeholder: string; type?: string }[];
};

type IntegrationGroup = { title: string; integrations: IntegrationDef[] };

const INTEGRATION_GROUPS: IntegrationGroup[] = [
  {
    title: "Identity & Access",
    integrations: [
      {
        type: "google_workspace", label: "Google Workspace",
        description: "Collect users, admin accounts, and groups via Admin SDK",
        fields: [
          { key: "admin_email", label: "Admin Email", placeholder: "admin@yourcompany.com" },
          { key: "service_account_json", label: "Service Account JSON", placeholder: '{"type":"service_account",...}', type: "textarea" },
        ],
      },
      {
        type: "okta", label: "Okta",
        description: "Collect users, groups, and password & MFA policies",
        fields: [
          { key: "domain", label: "Okta Domain", placeholder: "mycompany.okta.com" },
          { key: "api_token", label: "API Token", placeholder: "••••••••••••", type: "password" },
        ],
      },
      {
        type: "azure_ad", label: "Microsoft Entra ID",
        description: "Collect users, groups, and directory role assignments",
        fields: [
          { key: "tenant_id", label: "Tenant ID", placeholder: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" },
          { key: "client_id", label: "Client ID", placeholder: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" },
          { key: "client_secret", label: "Client Secret", placeholder: "••••••••••••", type: "password" },
        ],
      },
      {
        type: "rippling", label: "Rippling",
        description: "Sync employee lifecycle events and offboarding for access reviews",
        comingSoon: true,
      },
    ],
  },
  {
    title: "Cloud Infrastructure",
    integrations: [
      {
        type: "aws", label: "Amazon Web Services",
        description: "Collect IAM users, policies, CloudTrail logs, and S3 configs",
        fields: [
          { key: "access_key_id", label: "Access Key ID", placeholder: "AKIAIOSFODNN7EXAMPLE" },
          { key: "secret_access_key", label: "Secret Access Key", placeholder: "••••••••••••", type: "password" },
          { key: "region", label: "Region", placeholder: "us-east-1" },
        ],
      },
      {
        type: "google_cloud", label: "Google Cloud Platform",
        description: "Collect IAM policies, audit logs, and resource configurations",
        comingSoon: true,
      },
    ],
  },
  {
    title: "Source Control",
    integrations: [
      {
        type: "github", label: "GitHub",
        description: "Collect repositories, members, admin users, and branch protection rules",
        fields: [
          { key: "token", label: "Personal Access Token", placeholder: "ghp_••••••••", type: "password" },
          { key: "org", label: "Organization", placeholder: "my-org" },
        ],
      },
      {
        type: "gitlab", label: "GitLab",
        description: "Collect projects, members, and merge request approval settings",
        comingSoon: true,
      },
    ],
  },
  {
    title: "Project Management",
    integrations: [
      {
        type: "jira", label: "Jira",
        description: "Collect projects, users, and change tickets for change management evidence",
        fields: [
          { key: "domain", label: "Domain", placeholder: "mycompany.atlassian.net" },
          { key: "email", label: "Admin Email", placeholder: "admin@mycompany.com" },
          { key: "api_token", label: "API Token", placeholder: "••••••••••••", type: "password" },
        ],
      },
      {
        type: "linear", label: "Linear",
        description: "Collect issues, cycles, and team members for change tracking evidence",
        comingSoon: true,
      },
      {
        type: "notion", label: "Notion",
        description: "Sync policy documents and runbooks as compliance evidence",
        comingSoon: true,
      },
    ],
  },
  {
    title: "Communication",
    integrations: [
      {
        type: "slack", label: "Slack",
        description: "Collect workspace users, admin users, and channel retention policies",
        fields: [
          { key: "bot_token", label: "Bot Token", placeholder: "xoxb-••••••••", type: "password" },
        ],
      },
      {
        type: "microsoft_teams", label: "Microsoft Teams",
        description: "Collect team members, admin roles, and messaging policies",
        comingSoon: true,
      },
    ],
  },
  {
    title: "Monitoring & Security",
    integrations: [
      {
        type: "datadog", label: "Datadog",
        description: "Pull audit logs, alert rules, and monitoring coverage as evidence",
        comingSoon: true,
      },
      {
        type: "pagerduty", label: "PagerDuty",
        description: "Collect on-call schedules and incident response records",
        comingSoon: true,
      },
      {
        type: "sentry", label: "Sentry",
        description: "Collect error monitoring configuration and team access records",
        comingSoon: true,
      },
      {
        type: "stripe", label: "Stripe",
        description: "Collect payment security settings for PCI DSS evidence",
        comingSoon: true,
      },
    ],
  },
  {
    title: "HR & People",
    integrations: [
      {
        type: "bamboohr", label: "BambooHR",
        description: "Sync employee records and offboarding workflows",
        comingSoon: true,
      },
    ],
  },
];

const ALL_DEFS: IntegrationDef[] = INTEGRATION_GROUPS.flatMap((g) => g.integrations);

// ── Upgrade Modal ─────────────────────────────────────────────────────────────
function UpgradeModal({ onClose }: { onClose: () => void }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const handleUpgrade = async () => {
    setLoading(true);
    try {
      const { checkout_url } = await api.createCheckout();
      window.location.href = checkout_url;
    } catch { router.push("/settings"); }
  };
  return (
    <div className="fixed inset-0 bg-black/40 flex items-end sm:items-center justify-center z-50 p-0 sm:p-4">
      <div className="bg-white rounded-t-2xl sm:rounded-2xl shadow-xl w-full sm:max-w-md p-6 relative">
        <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"><X className="w-5 h-5"/></button>
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center shrink-0">
            <Lock className="w-5 h-5 text-amber-600"/>
          </div>
          <div>
            <h2 className="text-base font-semibold text-gray-900">Integration limit reached</h2>
            <p className="text-sm text-gray-500">Free plan allows up to {FREE_LIMIT} integrations.</p>
          </div>
        </div>
        <div className="bg-gradient-to-br from-teal-50 to-emerald-50 border border-teal-200 rounded-xl p-4 mb-5">
          <p className="text-sm font-semibold text-teal-800 mb-2">Upgrade to Growth — $149/mo</p>
          <ul className="space-y-1 text-sm text-teal-700">
            {["Unlimited integrations", "AI Compliance Advisor", "SOC 2, ISO 27001, GDPR, PCI DSS", "Priority support"].map((f) => (
              <li key={f} className="flex items-center gap-2"><Zap className="w-3.5 h-3.5 shrink-0"/> {f}</li>
            ))}
          </ul>
        </div>
        <div className="flex gap-3">
          <button onClick={onClose} className="flex-1 border border-gray-200 text-gray-700 rounded-xl px-4 py-2 text-sm hover:bg-gray-50">Cancel</button>
          <button onClick={handleUpgrade} disabled={loading} className="flex-1 flex items-center justify-center gap-1.5 bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white font-medium rounded-xl px-4 py-2 text-sm">
            <Zap className="w-4 h-4"/>{loading ? "Loading…" : "Upgrade now"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Connect Modal ─────────────────────────────────────────────────────────────
function ConnectModal({ def, onClose, onConnected, onUpgradeNeeded }: {
  def: IntegrationDef; onClose: () => void; onConnected: () => void; onUpgradeNeeded: () => void;
}) {
  const [fields, setFields] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setError(""); setLoading(true);
    try {
      await api.connectIntegration(def.type, fields);
      onConnected(); onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Connection failed";
      if (msg.toLowerCase().includes("free plan") || msg.toLowerCase().includes("upgrade")) { onClose(); onUpgradeNeeded(); }
      else setError(msg);
    } finally { setLoading(false); }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-end sm:items-center justify-center z-50 p-0 sm:p-4">
      <div className="bg-white rounded-t-2xl sm:rounded-2xl shadow-xl w-full sm:max-w-md p-5 sm:p-6 relative max-h-[90vh] overflow-y-auto">
        <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"><X className="w-5 h-5"/></button>
        <div className="flex items-center gap-3 mb-5">
          <LogoBadge type={def.type} size={44}/>
          <div>
            <h2 className="text-base font-semibold text-gray-900">Connect {def.label}</h2>
            <p className="text-sm text-gray-500">{def.description}</p>
          </div>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm">{error}</div>}
          {(def.fields ?? []).map((f) => (
            <div key={f.key}>
              <label className="block text-sm font-medium text-gray-700 mb-1">{f.label}</label>
              {f.type === "textarea" ? (
                <textarea placeholder={f.placeholder} required rows={5} value={fields[f.key] ?? ""}
                  onChange={(e) => setFields((p) => ({ ...p, [f.key]: e.target.value }))}
                  className="w-full border border-gray-200 rounded-xl px-3 py-2 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-brand-500/30 resize-none"/>
              ) : (
                <input type={f.type ?? "text"} placeholder={f.placeholder} required value={fields[f.key] ?? ""}
                  onChange={(e) => setFields((p) => ({ ...p, [f.key]: e.target.value }))}
                  className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"/>
              )}
            </div>
          ))}
          <div className="flex gap-3 pt-1">
            <button type="button" onClick={onClose} className="flex-1 border border-gray-200 text-gray-700 rounded-xl px-4 py-2 text-sm hover:bg-gray-50">Cancel</button>
            <button type="submit" disabled={loading} className="flex-1 bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white font-medium rounded-xl px-4 py-2 text-sm">
              {loading ? "Connecting…" : "Connect"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Status badge ──────────────────────────────────────────────────────────────
function StatusBadge({ status }: { status: string }) {
  if (status === "active") return (
    <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-100 px-2 py-0.5 rounded-full">
      <CheckCircle2 className="w-3 h-3"/> Active
    </span>
  );
  if (status === "error") return (
    <span className="flex items-center gap-1 text-[11px] font-semibold text-red-700 bg-red-50 border border-red-100 px-2 py-0.5 rounded-full">
      <AlertCircle className="w-3 h-3"/> Error
    </span>
  );
  return (
    <span className="flex items-center gap-1 text-[11px] font-semibold text-amber-700 bg-amber-50 border border-amber-100 px-2 py-0.5 rounded-full">
      <Clock className="w-3 h-3"/> Pending
    </span>
  );
}

// ── Integration card ──────────────────────────────────────────────────────────
function IntegrationCard({ def, connected, canConnect, collecting, onConnect, onCollect, onDisconnect, onUpgrade }: {
  def: IntegrationDef; connected?: Integration; canConnect: boolean; collecting: boolean;
  onConnect: () => void; onCollect: () => void; onDisconnect: () => void; onUpgrade: () => void;
}) {
  return (
    <div className={`bg-white rounded-2xl border p-4 flex items-center gap-4 transition-shadow ${
      connected ? "border-gray-100 shadow-card" : def.comingSoon ? "border-gray-100 opacity-60" : "border-gray-100 hover:shadow-sm"
    }`}>
      <LogoBadge type={def.type} size={44}/>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap mb-0.5">
          <span className="font-semibold text-sm text-gray-900">{def.label}</span>
          {connected && <StatusBadge status={connected.status}/>}
          {def.comingSoon && (
            <span className="text-[10px] font-bold uppercase tracking-wide text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded-md">Soon</span>
          )}
        </div>
        <p className="text-xs text-gray-500 leading-relaxed line-clamp-2">{def.description}</p>
        {connected?.last_error && <p className="text-xs text-red-500 mt-1 truncate">{connected.last_error}</p>}
        {connected?.last_collected_at && (
          <p className="text-[11px] text-gray-400 mt-0.5">Synced {new Date(connected.last_collected_at).toLocaleString()}</p>
        )}
      </div>
      <div className="flex items-center gap-1.5 shrink-0 ml-2">
        {def.comingSoon ? null : connected ? (
          <>
            <button onClick={onCollect} disabled={collecting} title="Sync now"
              className="p-2 text-gray-400 hover:text-brand-600 hover:bg-brand-50 rounded-xl transition-colors disabled:opacity-40">
              <RefreshCw className={`w-4 h-4 ${collecting ? "animate-spin" : ""}`}/>
            </button>
            <button onClick={onConnect} className="px-3 py-1.5 text-xs font-semibold border border-gray-200 text-gray-600 hover:bg-gray-50 rounded-xl transition-colors">
              Reconnect
            </button>
            <button onClick={onDisconnect} title="Disconnect"
              className="p-2 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-xl transition-colors">
              <Trash2 className="w-4 h-4"/>
            </button>
          </>
        ) : !canConnect ? (
          <button onClick={onUpgrade} className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-600 text-xs font-semibold rounded-xl transition-colors">
            <Lock className="w-3.5 h-3.5"/> Upgrade
          </button>
        ) : (
          <button onClick={onConnect} className="flex items-center gap-1.5 px-3 py-1.5 bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold rounded-xl transition-colors">
            <Plus className="w-3.5 h-3.5"/> Connect
          </button>
        )}
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function IntegrationsPage() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [billing, setBilling] = useState<BillingInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState<string | null>(null);
  const [collecting, setCollecting] = useState<string | null>(null);
  const [showUpgrade, setShowUpgrade] = useState(false);
  const [toast, setToast] = useState("");
  const [search, setSearch] = useState("");

  const load = () =>
    Promise.all([api.getIntegrations(), api.getSubscription()])
      .then(([ints, bill]) => { setIntegrations(ints); setBilling(bill); })
      .catch(console.error)
      .finally(() => setLoading(false));

  useEffect(() => { load(); }, []);

  const showToast = (msg: string) => { setToast(msg); setTimeout(() => setToast(""), 3000); };

  const handleCollect = async (type: string) => {
    setCollecting(type);
    try { await api.triggerCollect(type); showToast(`Sync started for ${type}`); }
    catch (err: unknown) { showToast(err instanceof Error ? err.message : "Failed to start sync"); }
    finally { setCollecting(null); }
  };

  const handleDisconnect = async (type: string) => {
    if (!confirm(`Disconnect ${type}? This will remove the stored credentials.`)) return;
    try { await api.disconnectIntegration(type); await load(); showToast(`${type} disconnected`); }
    catch (err: unknown) { showToast(err instanceof Error ? err.message : "Failed to disconnect"); }
  };

  const isFreePlan = billing?.plan === "free";
  const atLimit = isFreePlan && integrations.length >= FREE_LIMIT;
  const connectingDef = ALL_DEFS.find((d) => d.type === connecting);

  const query = search.toLowerCase();
  const filteredGroups = INTEGRATION_GROUPS.map((g) => ({
    ...g,
    integrations: g.integrations.filter(
      (d) => !query || d.label.toLowerCase().includes(query) || d.description.toLowerCase().includes(query)
    ),
  })).filter((g) => g.integrations.length > 0);

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin"/>
    </div>
  );

  return (
    <div className="animate-fade-in overflow-x-hidden">
      {toast && (
        <div className="fixed top-4 right-4 bg-gray-900 text-white text-sm px-4 py-2.5 rounded-xl shadow-lg z-50">
          {toast}
        </div>
      )}

      {showUpgrade && <UpgradeModal onClose={() => setShowUpgrade(false)}/>}
      {connecting && connectingDef && (
        <ConnectModal def={connectingDef} onClose={() => setConnecting(null)} onConnected={load} onUpgradeNeeded={() => setShowUpgrade(true)}/>
      )}

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Integrations</h1>
          <p className="text-sm text-gray-500 mt-0.5">Connect your tools to automatically collect compliance evidence.</p>
        </div>
        {integrations.length > 0 && (
          <span className="text-sm text-gray-400 mt-1">
            <span className="font-semibold text-gray-700">{integrations.length}</span> connected
          </span>
        )}
      </div>

      {/* Usage bar — free plan */}
      {isFreePlan && (
        <div className="bg-white border border-gray-100 shadow-card rounded-2xl p-4 mb-6 flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4">
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-sm font-medium text-gray-700">{integrations.length} / {FREE_LIMIT} integrations used</span>
              {atLimit && <span className="text-xs text-red-600 font-semibold">Limit reached</span>}
            </div>
            <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div className={`h-full rounded-full transition-all ${atLimit ? "bg-red-400" : integrations.length >= 2 ? "bg-amber-400" : "bg-brand-500"}`}
                style={{ width: `${Math.min((integrations.length / FREE_LIMIT) * 100, 100)}%` }}/>
            </div>
          </div>
          <button onClick={() => setShowUpgrade(true)}
            className="flex items-center gap-1.5 text-xs font-semibold text-brand-600 bg-brand-50 hover:bg-brand-100 px-3 py-2 rounded-xl transition-colors shrink-0">
            <Zap className="w-3.5 h-3.5"/> Upgrade for unlimited
          </button>
        </div>
      )}

      {/* Search */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
        <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search integrations…"
          className="w-full pl-9 pr-4 py-2.5 text-sm border border-gray-200 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/30"/>
      </div>

      {/* Groups */}
      <div className="space-y-8">
        {filteredGroups.map((group) => (
          <div key={group.title}>
            <h2 className="text-[11px] font-semibold uppercase tracking-widest text-gray-400 mb-3">{group.title}</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {group.integrations.map((def) => {
                const connected = integrations.find((i) => i.integration_type === def.type);
                return (
                  <IntegrationCard key={def.type} def={def} connected={connected}
                    canConnect={!atLimit || !!connected}
                    collecting={collecting === def.type}
                    onConnect={() => setConnecting(def.type)}
                    onCollect={() => handleCollect(def.type)}
                    onDisconnect={() => handleDisconnect(def.type)}
                    onUpgrade={() => setShowUpgrade(true)}
                  />
                );
              })}
            </div>
          </div>
        ))}
        {filteredGroups.length === 0 && (
          <div className="text-center py-16 text-gray-400">
            <Search className="w-8 h-8 mx-auto mb-3 opacity-40"/>
            <p className="text-sm">No integrations match &ldquo;{search}&rdquo;</p>
          </div>
        )}
      </div>
    </div>
  );
}

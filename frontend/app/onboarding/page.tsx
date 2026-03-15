"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { useAuth } from "@/components/auth-provider";
import { api } from "@/lib/api";
import {
  ArrowRight,
  ArrowLeft,
  Check,
  Shield,
  Globe,
  CreditCard,
  Building2,
  Plug,
  X,
  ChevronRight,
  Sparkles,
  Users,
} from "lucide-react";

// ── Frameworks ────────────────────────────────────────────────────────────────
const FRAMEWORKS = [
  {
    id: "soc2",
    label: "SOC 2",
    description: "Trust Services Criteria for security, availability & confidentiality",
    icon: Shield,
    color: "from-blue-500 to-blue-600",
    popular: true,
  },
  {
    id: "iso27001",
    label: "ISO 27001",
    description: "International standard for information security management",
    icon: Globe,
    color: "from-emerald-500 to-emerald-600",
    popular: false,
  },
  {
    id: "gdpr",
    label: "GDPR",
    description: "EU data protection and privacy regulation",
    icon: Building2,
    color: "from-purple-500 to-purple-600",
    popular: false,
  },
  {
    id: "pci_dss",
    label: "PCI DSS",
    description: "Payment card industry data security standards",
    icon: CreditCard,
    color: "from-rose-500 to-rose-600",
    popular: false,
  },
];

// ── Quick integrations ─────────────────────────────────────────────────────────
type IntegrationDef = {
  type: string;
  label: string;
  description: string;
  fields: { key: string; label: string; placeholder: string; type?: string }[];
};

const QUICK_INTEGRATIONS: IntegrationDef[] = [
  {
    type: "github",
    label: "GitHub",
    description: "Repos, members, branch protection",
    fields: [
      { key: "token", label: "Personal Access Token", placeholder: "ghp_••••••••", type: "password" },
      { key: "org", label: "Organization", placeholder: "my-org" },
    ],
  },
  {
    type: "aws",
    label: "Amazon Web Services",
    description: "IAM, CloudTrail, S3 configuration",
    fields: [
      { key: "access_key_id", label: "Access Key ID", placeholder: "AKIAIOSFODNN7EXAMPLE" },
      { key: "secret_access_key", label: "Secret Access Key", placeholder: "••••••••••••", type: "password" },
      { key: "region", label: "Region", placeholder: "us-east-1" },
    ],
  },
  {
    type: "slack",
    label: "Slack",
    description: "Workspace users, admin accounts",
    fields: [
      { key: "bot_token", label: "Bot Token", placeholder: "xoxb-••••••••", type: "password" },
    ],
  },
  {
    type: "google_workspace",
    label: "Google Workspace",
    description: "Users, admin accounts, groups",
    fields: [
      { key: "admin_email", label: "Admin Email", placeholder: "admin@yourcompany.com" },
      { key: "service_account_json", label: "Service Account JSON", placeholder: '{"type":"service_account",...}', type: "textarea" },
    ],
  },
];

// ── Inline SVG logos ───────────────────────────────────────────────────────────
type LogoCfg = { bg: string; svg?: (s: number) => React.ReactNode };

const LOGO_CONFIG: Record<string, LogoCfg> = {
  github: {
    bg: "#24292E",
    svg: (s) => {
      const cx = s / 2, cy = s / 2, r = s * 0.29;
      return (
        <>
          <circle cx={cx} cy={cy} r={r} fill="white" />
          <circle cx={cx} cy={cy - r * 0.07} r={r * 0.62} fill="#24292E" />
          <ellipse cx={cx - r * 0.42} cy={cy - r * 0.58} rx={r * 0.19} ry={r * 0.24} fill="white" />
          <ellipse cx={cx + r * 0.42} cy={cy - r * 0.58} rx={r * 0.19} ry={r * 0.24} fill="white" />
        </>
      );
    },
  },
  aws: {
    bg: "#232F3E",
    svg: (s) => (
      <>
        <text x={s / 2} y={s * 0.46} textAnchor="middle" dominantBaseline="central" fill="white" fontFamily="system-ui" fontWeight="800" fontSize={s * 0.27}>AWS</text>
        <path d={`M${s * 0.27} ${s * 0.67} Q${s * 0.5} ${s * 0.78} ${s * 0.73} ${s * 0.67}`} stroke="#FF9900" strokeWidth={s * 0.07} strokeLinecap="round" fill="none" />
      </>
    ),
  },
  slack: {
    bg: "#4A154B",
    svg: (s) => {
      const c = s / 2, r = s * 0.13, g = s * 0.06;
      return (
        <>
          <rect x={c - r * 2 - g / 2} y={c - r * 2 - g / 2} width={r * 2} height={r * 2} rx={r * 0.5} fill="#E01E5A" />
          <rect x={c + g / 2} y={c - r * 2 - g / 2} width={r * 2} height={r * 2} rx={r * 0.5} fill="#36C5F0" />
          <rect x={c - r * 2 - g / 2} y={c + g / 2} width={r * 2} height={r * 2} rx={r * 0.5} fill="#2EB67D" />
          <rect x={c + g / 2} y={c + g / 2} width={r * 2} height={r * 2} rx={r * 0.5} fill="#ECB22E" />
        </>
      );
    },
  },
  google_workspace: {
    bg: "#FFFFFF",
    svg: (s) => {
      const cx = s / 2, cy = s / 2, r = s * 0.29, gx = cx + r * 0.15;
      return (
        <>
          <rect width={s} height={s} rx={Math.round(s * 0.25)} fill="white" stroke="#E5E7EB" strokeWidth="1.5" />
          <path d={`M${gx} ${cy} L${gx} ${cy - r * 0.55} L${cx - r * 0.35} ${cy - r * 0.55}`} stroke="#4285F4" strokeWidth={s * 0.09} strokeLinecap="round" fill="none" />
          <path d={`M${cx - r} ${cy} A${r} ${r} 0 1 1 ${cx + r * 0.7} ${cy + r * 0.7}`} stroke="#EA4335" strokeWidth={s * 0.09} fill="none" strokeLinecap="round" />
          <path d={`M${cx + r * 0.7} ${cy + r * 0.7} A${r} ${r} 0 0 1 ${cx + r} ${cy}`} stroke="#FBBC05" strokeWidth={s * 0.09} fill="none" strokeLinecap="round" />
          <line x1={cx} y1={cy} x2={gx} y2={cy} stroke="#34A853" strokeWidth={s * 0.09} strokeLinecap="round" />
        </>
      );
    },
  },
};

function LogoBadge({ type, size = 38 }: { type: string; size?: number }) {
  const cfg = LOGO_CONFIG[type] ?? { bg: "#6B7280" };
  const s = size;
  const r = Math.round(s * 0.25);
  return (
    <svg width={s} height={s} viewBox={`0 0 ${s} ${s}`} fill="none" xmlns="http://www.w3.org/2000/svg" className="shrink-0">
      <rect width={s} height={s} rx={r} fill={cfg.bg} />
      {cfg.svg?.(s)}
    </svg>
  );
}

// ── Step dots ─────────────────────────────────────────────────────────────────
function StepDots({ current, total }: { current: number; total: number }) {
  return (
    <div className="flex items-center gap-2">
      {Array.from({ length: total }).map((_, i) => (
        <div
          key={i}
          className={`rounded-full transition-all duration-300 ${
            i === current
              ? "w-6 h-2 bg-brand-400"
              : i < current
              ? "w-2 h-2 bg-brand-500"
              : "w-2 h-2 bg-white/20"
          }`}
        />
      ))}
    </div>
  );
}

const TOTAL_STEPS = 4;

export default function OnboardingPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  const [step, setStep] = useState(0);
  const [frameworks, setFrameworks] = useState<string[]>(["soc2"]);
  const [connectingType, setConnectingType] = useState<string | null>(null);
  const [connectFields, setConnectFields] = useState<Record<string, string>>({});
  const [connectLoading, setConnectLoading] = useState(false);
  const [connectError, setConnectError] = useState("");
  const [connectedTypes, setConnectedTypes] = useState<string[]>([]);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<"member" | "admin">("member");
  const [inviteSent, setInviteSent] = useState(false);
  const [inviteLoading, setInviteLoading] = useState(false);
  const [inviteError, setInviteError] = useState("");
  const [completing, setCompleting] = useState(false);

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [user, loading, router]);

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-brand-400 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const toggleFramework = (id: string) => {
    setFrameworks((prev) =>
      prev.includes(id) ? (prev.length > 1 ? prev.filter((f) => f !== id) : prev) : [...prev, id]
    );
  };

  const handleConnect = async (def: IntegrationDef) => {
    setConnectLoading(true);
    setConnectError("");
    try {
      await api.connectIntegration(def.type, connectFields);
      setConnectedTypes((p) => [...p, def.type]);
      setConnectingType(null);
      setConnectFields({});
    } catch (err: unknown) {
      setConnectError(err instanceof Error ? err.message : "Connection failed");
    } finally {
      setConnectLoading(false);
    }
  };

  const handleInvite = async () => {
    if (!inviteEmail.trim()) return;
    setInviteLoading(true);
    setInviteError("");
    try {
      await api.createInvite(inviteEmail.trim(), inviteRole);
      setInviteSent(true);
      setInviteEmail("");
    } catch (err: unknown) {
      setInviteError(err instanceof Error ? err.message : "Failed to send invite");
    } finally {
      setInviteLoading(false);
    }
  };

  const handleComplete = async () => {
    setCompleting(true);
    try {
      await api.completeOnboarding();
      sessionStorage.setItem("onboarding_done", "true");
    } catch {
      // non-fatal
    }
    router.push("/dashboard");
  };

  const connectingDef = QUICK_INTEGRATIONS.find((d) => d.type === connectingType);

  return (
    <div className="flex-1 flex flex-col min-h-screen">
      {/* Top bar */}
      <div className="flex items-center justify-between px-6 py-5 shrink-0">
        <div className="flex items-center gap-2.5">
          <Image src="/logo-icon.png" alt="TraceLayer" width={28} height={28} className="rounded-lg" />
          <span className="text-base font-bold text-white tracking-tight">TraceLayer</span>
        </div>
        <button
          onClick={handleComplete}
          disabled={completing}
          className="text-xs text-white/40 hover:text-white/70 transition-colors"
        >
          Skip setup
        </button>
      </div>

      {/* Main */}
      <div className="flex-1 flex flex-col items-center justify-center px-4 py-8">
        <div className="mb-8">
          <StepDots current={step} total={TOTAL_STEPS} />
        </div>

        <div className="w-full max-w-lg">

          {/* ── Step 0: Welcome ─────────────────────────────────────── */}
          {step === 0 && (
            <div className="text-center">
              <div className="w-20 h-20 bg-brand-500/20 rounded-3xl flex items-center justify-center mx-auto mb-6 ring-1 ring-brand-400/30">
                <Sparkles className="w-9 h-9 text-brand-300" />
              </div>
              <h1 className="text-3xl font-bold text-white mb-3">
                Welcome to TraceLayer
              </h1>
              <p className="text-brand-200 text-base leading-relaxed mb-2">
                Hi <span className="font-semibold text-white">{user.email.split("@")[0]}</span> — let&apos;s get your compliance program running.
              </p>
              <p className="text-white/40 text-sm mb-10">
                This takes about 3 minutes. You can skip any step.
              </p>

              <div className="grid grid-cols-3 gap-3 mb-10">
                {[
                  { icon: Shield, label: "Pick your framework" },
                  { icon: Plug, label: "Connect tools" },
                  { icon: Users, label: "Invite your team" },
                ].map(({ icon: Icon, label }) => (
                  <div key={label} className="bg-white/5 rounded-2xl p-4 flex flex-col items-center gap-2.5 border border-white/8">
                    <Icon className="w-5 h-5 text-brand-300" />
                    <span className="text-xs text-brand-200/80 font-medium text-center leading-tight">{label}</span>
                  </div>
                ))}
              </div>

              <button
                onClick={() => setStep(1)}
                className="w-full flex items-center justify-center gap-2 bg-brand-500 hover:bg-brand-400 text-white font-semibold rounded-2xl px-6 py-3.5 text-base transition-colors shadow-lg shadow-brand-950/50"
              >
                Get started <ArrowRight className="w-5 h-5" />
              </button>
            </div>
          )}

          {/* ── Step 1: Framework ────────────────────────────────────── */}
          {step === 1 && (
            <div>
              <div className="text-center mb-7">
                <h2 className="text-2xl font-bold text-white mb-2">Choose your framework</h2>
                <p className="text-white/50 text-sm">Select one or more. You can add more frameworks later.</p>
              </div>

              <div className="space-y-2.5 mb-7">
                {FRAMEWORKS.map((fw) => {
                  const selected = frameworks.includes(fw.id);
                  return (
                    <button
                      key={fw.id}
                      onClick={() => toggleFramework(fw.id)}
                      className={`w-full flex items-center gap-4 p-4 rounded-2xl border text-left transition-all ${
                        selected
                          ? "bg-white/10 border-brand-400/50"
                          : "bg-white/4 border-white/8 hover:bg-white/7 hover:border-white/15"
                      }`}
                    >
                      <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${fw.color} flex items-center justify-center shrink-0`}>
                        <fw.icon className="w-5 h-5 text-white" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-0.5">
                          <span className="font-semibold text-white text-sm">{fw.label}</span>
                          {fw.popular && (
                            <span className="text-[10px] font-bold uppercase tracking-wide text-brand-300 bg-brand-500/20 px-1.5 py-0.5 rounded-md">Popular</span>
                          )}
                        </div>
                        <p className="text-xs text-white/40 leading-relaxed">{fw.description}</p>
                      </div>
                      <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 transition-all ${
                        selected ? "bg-brand-400 border-brand-400" : "border-white/25"
                      }`}>
                        {selected && <Check className="w-3 h-3 text-white" strokeWidth={3} />}
                      </div>
                    </button>
                  );
                })}
              </div>

              <div className="flex gap-3">
                <button onClick={() => setStep(0)} className="flex items-center gap-2 px-5 py-3 text-white/50 hover:text-white transition-colors text-sm">
                  <ArrowLeft className="w-4 h-4" /> Back
                </button>
                <button
                  onClick={() => setStep(2)}
                  className="flex-1 flex items-center justify-center gap-2 bg-brand-500 hover:bg-brand-400 text-white font-semibold rounded-2xl px-6 py-3 text-sm transition-colors"
                >
                  Continue <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* ── Step 2: Connect integration ───────────────────────────── */}
          {step === 2 && (
            <div>
              <div className="text-center mb-7">
                <h2 className="text-2xl font-bold text-white mb-2">Connect your first tool</h2>
                <p className="text-white/50 text-sm">TraceLayer collects evidence automatically. You can connect more from Settings later.</p>
              </div>

              {connectingDef ? (
                <div className="bg-white/6 border border-white/10 rounded-2xl p-5 mb-4">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <LogoBadge type={connectingDef.type} size={36} />
                      <span className="font-semibold text-white text-sm">{connectingDef.label}</span>
                    </div>
                    <button
                      onClick={() => { setConnectingType(null); setConnectFields({}); setConnectError(""); }}
                      className="text-white/30 hover:text-white/60 transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  {connectError && (
                    <div className="bg-red-500/10 border border-red-400/20 text-red-300 rounded-xl px-3 py-2 text-xs mb-3">{connectError}</div>
                  )}
                  <div className="space-y-3 mb-4">
                    {connectingDef.fields.map((f) => (
                      <div key={f.key}>
                        <label className="block text-xs font-medium text-white/60 mb-1">{f.label}</label>
                        {f.type === "textarea" ? (
                          <textarea
                            placeholder={f.placeholder}
                            rows={4}
                            value={connectFields[f.key] ?? ""}
                            onChange={(e) => setConnectFields((p) => ({ ...p, [f.key]: e.target.value }))}
                            className="w-full bg-white/5 border border-white/12 rounded-xl px-3 py-2 text-xs font-mono text-white placeholder-white/25 focus:outline-none focus:ring-2 focus:ring-brand-400/30 resize-none"
                          />
                        ) : (
                          <input
                            type={f.type ?? "text"}
                            placeholder={f.placeholder}
                            value={connectFields[f.key] ?? ""}
                            onChange={(e) => setConnectFields((p) => ({ ...p, [f.key]: e.target.value }))}
                            className="w-full bg-white/5 border border-white/12 rounded-xl px-3 py-2 text-sm text-white placeholder-white/25 focus:outline-none focus:ring-2 focus:ring-brand-400/30"
                          />
                        )}
                      </div>
                    ))}
                  </div>
                  <button
                    onClick={() => handleConnect(connectingDef)}
                    disabled={connectLoading}
                    className="w-full bg-brand-500 hover:bg-brand-400 disabled:opacity-60 text-white font-semibold rounded-xl py-2.5 text-sm transition-colors"
                  >
                    {connectLoading ? "Connecting…" : `Connect ${connectingDef.label}`}
                  </button>
                </div>
              ) : (
                <div className="space-y-2 mb-4">
                  {QUICK_INTEGRATIONS.map((def) => {
                    const done = connectedTypes.includes(def.type);
                    return (
                      <button
                        key={def.type}
                        onClick={() => { if (!done) { setConnectingType(def.type); setConnectFields({}); setConnectError(""); } }}
                        className={`w-full flex items-center gap-3 p-3.5 rounded-2xl border text-left transition-all ${
                          done
                            ? "bg-brand-500/10 border-brand-400/30"
                            : "bg-white/4 border-white/8 hover:bg-white/7 hover:border-white/15"
                        }`}
                      >
                        <LogoBadge type={def.type} size={36} />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-semibold text-white">{def.label}</p>
                          <p className="text-xs text-white/40 truncate">{def.description}</p>
                        </div>
                        {done ? (
                          <div className="w-6 h-6 rounded-full bg-brand-500 flex items-center justify-center shrink-0">
                            <Check className="w-3.5 h-3.5 text-white" strokeWidth={3} />
                          </div>
                        ) : (
                          <ChevronRight className="w-4 h-4 text-white/25 shrink-0" />
                        )}
                      </button>
                    );
                  })}
                </div>
              )}

              {!connectingDef && (
                <div className="flex gap-3">
                  <button onClick={() => setStep(1)} className="flex items-center gap-2 px-5 py-3 text-white/50 hover:text-white transition-colors text-sm">
                    <ArrowLeft className="w-4 h-4" /> Back
                  </button>
                  <button
                    onClick={() => setStep(3)}
                    className="flex-1 flex items-center justify-center gap-2 bg-brand-500 hover:bg-brand-400 text-white font-semibold rounded-2xl px-6 py-3 text-sm transition-colors"
                  >
                    {connectedTypes.length > 0 ? "Continue" : "Skip for now"} <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          )}

          {/* ── Step 3: Invite team ────────────────────────────────────── */}
          {step === 3 && (
            <div>
              <div className="text-center mb-7">
                <div className="w-16 h-16 bg-brand-500/20 rounded-2xl flex items-center justify-center mx-auto mb-5 ring-1 ring-brand-400/25">
                  <Users className="w-7 h-7 text-brand-300" />
                </div>
                <h2 className="text-2xl font-bold text-white mb-2">Invite your team</h2>
                <p className="text-white/50 text-sm">Add colleagues to collaborate on your compliance program.</p>
              </div>

              <div className="bg-white/5 border border-white/10 rounded-2xl p-5 mb-6">
                <div className="flex gap-2 mb-3">
                  <input
                    type="email"
                    placeholder="colleague@company.com"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleInvite()}
                    className="flex-1 bg-white/5 border border-white/12 rounded-xl px-3 py-2.5 text-sm text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-brand-400/30"
                  />
                  <select
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value as "member" | "admin")}
                    className="bg-white/5 border border-white/12 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-brand-400/30"
                  >
                    <option value="member" className="bg-gray-900">Member</option>
                    <option value="admin" className="bg-gray-900">Admin</option>
                  </select>
                </div>

                {inviteError && <p className="text-xs text-red-300 mb-2">{inviteError}</p>}

                {inviteSent && (
                  <div className="flex items-center gap-2 text-xs text-brand-300 bg-brand-500/10 border border-brand-400/20 rounded-xl px-3 py-2 mb-2">
                    <Check className="w-3.5 h-3.5" /> Invite sent! Add another or continue.
                  </div>
                )}

                <button
                  onClick={handleInvite}
                  disabled={inviteLoading || !inviteEmail.trim()}
                  className="w-full bg-white/8 hover:bg-white/12 disabled:opacity-50 text-white font-medium rounded-xl py-2.5 text-sm transition-colors border border-white/10"
                >
                  {inviteLoading ? "Sending…" : "Send invite"}
                </button>
              </div>

              <div className="flex gap-3">
                <button onClick={() => setStep(2)} className="flex items-center gap-2 px-5 py-3 text-white/50 hover:text-white transition-colors text-sm">
                  <ArrowLeft className="w-4 h-4" /> Back
                </button>
                <button
                  onClick={handleComplete}
                  disabled={completing}
                  className="flex-1 flex items-center justify-center gap-2 bg-brand-500 hover:bg-brand-400 disabled:opacity-60 text-white font-semibold rounded-2xl px-6 py-3 text-sm transition-colors"
                >
                  {completing ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Setting up…
                    </>
                  ) : (
                    <>
                      Go to dashboard <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="py-4 text-center shrink-0">
        <p className="text-xs text-white/20">TraceLayer · Continuous Compliance Automation</p>
      </div>
    </div>
  );
}

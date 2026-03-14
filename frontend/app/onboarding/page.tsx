"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/components/auth-provider";
import {
  ArrowRight, CheckCircle2, Zap, Shield, BarChart3,
  Github, Cloud, MessageSquare, Globe, Users, LayoutGrid, Server,
} from "lucide-react";

// ── Integration definitions ───────────────────────────────────────────────────

const INTEGRATIONS = [
  {
    type: "github",
    name: "GitHub",
    icon: Github,
    color: "bg-gray-900",
    description: "Branch protection, code reviews, audit logs",
    fields: [{ key: "token", label: "Personal Access Token", placeholder: "ghp_...", type: "password" }],
  },
  {
    type: "aws",
    name: "AWS",
    icon: Cloud,
    color: "bg-orange-500",
    description: "IAM users, CloudTrail, S3, password policy",
    fields: [
      { key: "access_key_id",     label: "Access Key ID",     placeholder: "AKIA...",    type: "text"     },
      { key: "secret_access_key", label: "Secret Access Key", placeholder: "••••••••",   type: "password" },
      { key: "region",            label: "Region",            placeholder: "us-east-1",  type: "text"     },
    ],
  },
  {
    type: "slack",
    name: "Slack",
    icon: MessageSquare,
    color: "bg-purple-600",
    description: "Workspace audit logs, channel access",
    fields: [{ key: "bot_token", label: "Bot Token", placeholder: "xoxb-...", type: "password" }],
  },
  {
    type: "google",
    name: "Google Workspace",
    icon: Globe,
    color: "bg-blue-500",
    description: "Admin activity, user accounts",
    fields: [{ key: "service_account_json", label: "Service Account JSON", placeholder: '{"type": "service_account", ...}', type: "text" }],
  },
  {
    type: "okta",
    name: "Okta",
    icon: Users,
    color: "bg-blue-600",
    description: "Users, system log, authentication policies",
    fields: [
      { key: "domain", label: "Okta Domain", placeholder: "yourorg.okta.com", type: "text" },
      { key: "api_token", label: "API Token", placeholder: "••••••••", type: "password" },
    ],
  },
  {
    type: "jira",
    name: "Jira",
    icon: LayoutGrid,
    color: "bg-blue-700",
    description: "Project access, audit log",
    fields: [
      { key: "domain",    label: "Atlassian Domain", placeholder: "yourorg.atlassian.net", type: "text"     },
      { key: "email",     label: "Account Email",    placeholder: "you@company.com",        type: "text"     },
      { key: "api_token", label: "API Token",        placeholder: "••••••••",               type: "password" },
    ],
  },
  {
    type: "azure",
    name: "Azure AD",
    icon: Server,
    color: "bg-blue-500",
    description: "Users, audit log, sign-in activity",
    fields: [
      { key: "tenant_id",     label: "Tenant ID",     placeholder: "xxxxxxxx-...", type: "text"     },
      { key: "client_id",     label: "Client ID",     placeholder: "xxxxxxxx-...", type: "text"     },
      { key: "client_secret", label: "Client Secret", placeholder: "••••••••",    type: "password" },
    ],
  },
];

// ── Step components ───────────────────────────────────────────────────────────

function StepWelcome({ onNext }: { onNext: () => void }) {
  return (
    <div className="text-center max-w-md mx-auto">
      <div className="w-16 h-16 bg-teal-50 border border-teal-100 rounded-2xl flex items-center justify-center mx-auto mb-5">
        <Zap className="w-8 h-8 text-teal-600" />
      </div>
      <h1 className="text-2xl font-extrabold text-gray-900 mb-3">You&apos;re in. Let&apos;s get you audit-ready.</h1>
      <p className="text-gray-500 text-sm leading-relaxed mb-8">
        Connect your first tool and TraceLayer starts collecting compliance evidence automatically — mapped to SOC 2, ISO 27001, and HIPAA in real time.
      </p>
      <div className="grid grid-cols-1 gap-3 mb-8 text-left">
        {[
          { icon: Shield, title: "Automated evidence collection", desc: "IAM users, audit logs, repositories — collected every 24h without any manual work." },
          { icon: BarChart3, title: "Live compliance score", desc: "See your SOC 2 / ISO 27001 / HIPAA posture update automatically as evidence comes in." },
          { icon: CheckCircle2, title: "Audit-ready PDF reports", desc: "Generate a formatted report for your auditor in one click — any time." },
        ].map(({ icon: Icon, title, desc }) => (
          <div key={title} className="flex items-start gap-3 bg-gray-50 rounded-xl p-3.5 border border-gray-100">
            <div className="w-8 h-8 bg-white rounded-lg border border-gray-100 flex items-center justify-center shrink-0">
              <Icon className="w-4 h-4 text-teal-600" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-900">{title}</p>
              <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">{desc}</p>
            </div>
          </div>
        ))}
      </div>
      <button
        onClick={onNext}
        className="w-full flex items-center justify-center gap-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold py-3.5 rounded-xl transition-colors text-sm"
      >
        Connect your first tool <ArrowRight className="w-4 h-4" />
      </button>
    </div>
  );
}

function StepConnect({ onDone, onSkip }: { onDone: (integrationType: string) => void; onSkip: () => void }) {
  const [selected, setSelected] = useState<typeof INTEGRATIONS[0] | null>(null);
  const [credentials, setCredentials] = useState<Record<string, string>>({});
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState("");

  const handleConnect = async () => {
    if (!selected) return;
    setConnecting(true);
    setError("");
    try {
      await api.connectIntegration(selected.type, credentials);
      await api.triggerCollect(selected.type);
      onDone(selected.type);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Connection failed — check your credentials");
    } finally {
      setConnecting(false);
    }
  };

  if (selected) {
    const Icon = selected.icon;
    return (
      <div className="max-w-md mx-auto">
        <button
          onClick={() => { setSelected(null); setCredentials({}); setError(""); }}
          className="text-xs text-gray-400 hover:text-gray-600 mb-6 flex items-center gap-1 transition-colors"
        >
          ← Back to integrations
        </button>
        <div className="flex items-center gap-3 mb-6">
          <div className={`w-10 h-10 ${selected.color} rounded-xl flex items-center justify-center`}>
            <Icon className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="font-extrabold text-gray-900">Connect {selected.name}</h2>
            <p className="text-xs text-gray-500">{selected.description}</p>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl px-4 py-3 mb-4">
            {error}
          </div>
        )}

        <div className="space-y-3 mb-6">
          {selected.fields.map((f) => (
            <div key={f.key}>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">{f.label}</label>
              <input
                type={f.type}
                value={credentials[f.key] ?? ""}
                onChange={(e) => setCredentials((c) => ({ ...c, [f.key]: e.target.value }))}
                placeholder={f.placeholder}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-400 bg-white"
              />
            </div>
          ))}
        </div>

        <button
          onClick={handleConnect}
          disabled={connecting || selected.fields.some((f) => !credentials[f.key])}
          className="w-full flex items-center justify-center gap-2 bg-teal-600 hover:bg-teal-700 disabled:opacity-40 text-white font-semibold py-3 rounded-xl transition-colors text-sm"
        >
          {connecting ? (
            <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Connecting…</>
          ) : (
            <>Connect {selected.name} <ArrowRight className="w-4 h-4" /></>
          )}
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-7">
        <h2 className="text-xl font-extrabold text-gray-900 mb-2">Connect your first tool</h2>
        <p className="text-sm text-gray-500">Pick any tool your team uses. You can connect more later.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
        {INTEGRATIONS.map((integration) => {
          const Icon = integration.icon;
          return (
            <button
              key={integration.type}
              onClick={() => { setSelected(integration); setCredentials({}); }}
              className="flex items-center gap-3 bg-white border border-gray-200 rounded-xl p-4 text-left hover:border-teal-300 hover:shadow-md transition-all group"
            >
              <div className={`w-10 h-10 ${integration.color} rounded-xl flex items-center justify-center shrink-0`}>
                <Icon className="w-5 h-5 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-gray-900">{integration.name}</p>
                <p className="text-xs text-gray-400 truncate">{integration.description}</p>
              </div>
              <ArrowRight className="w-4 h-4 text-gray-300 group-hover:text-teal-500 transition-colors shrink-0" />
            </button>
          );
        })}
      </div>

      <div className="text-center">
        <button onClick={onSkip} className="text-xs text-gray-400 hover:text-gray-600 transition-colors">
          Skip for now — I&apos;ll connect from the integrations page
        </button>
      </div>
    </div>
  );
}

function StepDone({ connected, onFinish }: { connected: string | null; onFinish: () => void }) {
  const integration = INTEGRATIONS.find((i) => i.type === connected);
  const Icon = integration?.icon;

  return (
    <div className="text-center max-w-md mx-auto">
      <div className="w-16 h-16 bg-emerald-50 border border-emerald-100 rounded-2xl flex items-center justify-center mx-auto mb-5">
        <CheckCircle2 className="w-8 h-8 text-emerald-600" />
      </div>
      <h1 className="text-2xl font-extrabold text-gray-900 mb-3">
        {connected ? "You're all set!" : "Ready to go!"}
      </h1>

      {connected && integration && Icon ? (
        <div className="bg-emerald-50 border border-emerald-100 rounded-xl px-4 py-4 mb-6 text-left">
          <div className="flex items-center gap-3 mb-2">
            <div className={`w-8 h-8 ${integration.color} rounded-lg flex items-center justify-center`}>
              <Icon className="w-4 h-4 text-white" />
            </div>
            <p className="text-sm font-semibold text-gray-900">{integration.name} connected</p>
          </div>
          <p className="text-xs text-gray-500 leading-relaxed">
            Evidence collection has started. Your first results will appear in the dashboard within the next few hours. Check back to see your compliance score update.
          </p>
        </div>
      ) : (
        <p className="text-gray-500 text-sm mb-6 leading-relaxed">
          No problem — head to the Integrations page whenever you&apos;re ready to connect your tools.
        </p>
      )}

      <div className="space-y-2.5">
        <button
          onClick={onFinish}
          className="w-full flex items-center justify-center gap-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold py-3.5 rounded-xl transition-colors text-sm"
        >
          Go to my dashboard <ArrowRight className="w-4 h-4" />
        </button>
        <Link
          href="/integrations"
          className="block text-center text-xs text-gray-400 hover:text-gray-600 transition-colors py-2"
        >
          Connect more integrations →
        </Link>
      </div>
    </div>
  );
}

// ── Main ──────────────────────────────────────────────────────────────────────

const STEPS = ["Welcome", "Connect", "Done"] as const;

export default function OnboardingPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [connectedType, setConnectedType] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [user, loading, router]);

  useEffect(() => {
    // If user already has integrations, skip onboarding
    if (!user) return;
    api.getIntegrations().then((integrations) => {
      if (integrations.length > 0) router.replace("/dashboard");
    }).catch(() => {});
  }, [user, router]);

  if (loading || !user) return null;

  const progress = ((step + 1) / STEPS.length) * 100;

  return (
    <div className="min-h-screen bg-[#f7f1e8] flex flex-col font-[family:'Sora',_ui-sans-serif,_system-ui]">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-black/5">
        <div className="max-w-2xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Image src="/logo-icon.png" alt="TraceLayer" width={26} height={26} className="rounded-lg" />
            <span className="font-extrabold text-sm text-gray-900">TraceLayer</span>
          </div>
          <div className="flex items-center gap-3 text-xs text-gray-400">
            {STEPS.map((s, i) => (
              <div key={s} className="flex items-center gap-1.5">
                <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                  i < step ? "bg-teal-600 text-white" :
                  i === step ? "bg-teal-600 text-white" :
                  "bg-gray-200 text-gray-500"
                }`}>
                  {i < step ? "✓" : i + 1}
                </span>
                <span className={i === step ? "text-gray-900 font-medium" : ""}>{s}</span>
                {i < STEPS.length - 1 && <span className="text-gray-200 ml-1">›</span>}
              </div>
            ))}
          </div>
        </div>
        {/* Progress bar */}
        <div className="h-0.5 bg-gray-100">
          <div className="h-full bg-teal-500 transition-all duration-500" style={{ width: `${progress}%` }} />
        </div>
      </header>

      {/* Content */}
      <main className="flex-1 flex items-center justify-center p-6">
        <div className="w-full">
          {step === 0 && <StepWelcome onNext={() => setStep(1)} />}
          {step === 1 && (
            <StepConnect
              onDone={(type) => { setConnectedType(type); setStep(2); }}
              onSkip={() => setStep(2)}
            />
          )}
          {step === 2 && (
            <StepDone
              connected={connectedType}
              onFinish={() => router.push("/dashboard")}
            />
          )}
        </div>
      </main>

      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&display=swap');
      `}</style>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/components/auth-provider";
import {
  CheckCircle2,
  ArrowRight,
  Plug,
  ShieldCheck,
  Zap,
  X,
} from "lucide-react";

const STEPS = [
  { id: 1, label: "Welcome" },
  { id: 2, label: "Connect" },
  { id: 3, label: "Collect" },
];

const INTEGRATIONS = [
  {
    type: "aws",
    label: "Amazon Web Services",
    description: "IAM users, policies, CloudTrail logs",
    fields: [
      { key: "access_key_id", label: "Access Key ID", placeholder: "AKIAIOSFODNN7EXAMPLE" },
      { key: "secret_access_key", label: "Secret Access Key", placeholder: "••••••••", type: "password" },
      { key: "region", label: "Region", placeholder: "us-east-1" },
    ],
  },
  {
    type: "github",
    label: "GitHub",
    description: "Repositories, members, admin users",
    fields: [
      { key: "token", label: "Personal Access Token", placeholder: "ghp_••••••••", type: "password" },
      { key: "org", label: "Organization", placeholder: "my-org" },
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
  {
    type: "okta",
    label: "Okta",
    description: "Users, groups, password policies",
    fields: [
      { key: "domain", label: "Okta Domain", placeholder: "mycompany.okta.com" },
      { key: "api_token", label: "API Token", placeholder: "••••••••", type: "password" },
    ],
  },
  {
    type: "slack",
    label: "Slack",
    description: "Workspace users and admin users",
    fields: [
      { key: "bot_token", label: "Bot Token", placeholder: "xoxb-••••••••", type: "password" },
    ],
  },
];

function StepIndicator({ current }: { current: number }) {
  return (
    <div className="flex items-center gap-2 mb-8">
      {STEPS.map((s, i) => (
        <div key={s.id} className="flex items-center gap-2">
          <div
            className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
              current > s.id
                ? "bg-green-500 text-white"
                : current === s.id
                ? "bg-brand-600 text-white"
                : "bg-gray-100 text-gray-400"
            }`}
          >
            {current > s.id ? <CheckCircle2 className="w-4 h-4" /> : s.id}
          </div>
          <span
            className={`text-sm font-medium ${
              current === s.id ? "text-gray-900" : "text-gray-400"
            }`}
          >
            {s.label}
          </span>
          {i < STEPS.length - 1 && <div className="w-8 h-px bg-gray-200 mx-1" />}
        </div>
      ))}
    </div>
  );
}

// ── Step 1: Welcome ──────────────────────────────────────────────────────────
function StepWelcome({ name, onNext }: { name: string; onNext: () => void }) {
  return (
    <div className="text-center">
      <div className="w-16 h-16 bg-brand-50 rounded-2xl flex items-center justify-center mx-auto mb-6">
        <ShieldCheck className="w-8 h-8 text-brand-600" />
      </div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">
        Welcome to TraceLayer{name ? `, ${name}` : ""}!
      </h2>
      <p className="text-gray-500 mb-8 max-w-md mx-auto">
        You&apos;re 3 minutes away from your first compliance score. Let&apos;s connect
        your first integration and start collecting evidence automatically.
      </p>

      <div className="grid grid-cols-3 gap-4 mb-10 max-w-lg mx-auto">
        {[
          { icon: Plug, label: "Connect", sub: "Link your tools" },
          { icon: Zap, label: "Collect", sub: "Auto-gather evidence" },
          { icon: ShieldCheck, label: "Score", sub: "See your posture" },
        ].map(({ icon: Icon, label, sub }) => (
          <div key={label} className="bg-gray-50 rounded-xl p-4">
            <Icon className="w-5 h-5 text-brand-600 mx-auto mb-2" />
            <p className="text-sm font-semibold text-gray-900">{label}</p>
            <p className="text-xs text-gray-400 mt-0.5">{sub}</p>
          </div>
        ))}
      </div>

      <button
        onClick={onNext}
        className="inline-flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white font-medium px-6 py-2.5 rounded-lg transition-colors"
      >
        Get started <ArrowRight className="w-4 h-4" />
      </button>
    </div>
  );
}

// ── Step 2: Connect integration ──────────────────────────────────────────────
function StepConnect({ onNext }: { onNext: (type: string) => void }) {
  const [selected, setSelected] = useState<string | null>(null);
  const [fields, setFields] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const def = INTEGRATIONS.find((i) => i.type === selected);

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selected) return;
    setError("");
    setLoading(true);
    try {
      await api.connectIntegration(selected, fields);
      onNext(selected);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Connection failed");
    } finally {
      setLoading(false);
    }
  };

  if (selected && def) {
    return (
      <div>
        <button
          onClick={() => { setSelected(null); setFields({}); setError(""); }}
          className="flex items-center gap-1 text-sm text-gray-400 hover:text-gray-600 mb-6 transition-colors"
        >
          ← Back
        </button>
        <h2 className="text-xl font-bold text-gray-900 mb-1">Connect {def.label}</h2>
        <p className="text-gray-500 text-sm mb-6">{def.description}</p>

        <form onSubmit={handleConnect} className="space-y-4 max-w-md">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
              {error}
            </div>
          )}
          {def.fields.map((f) => (
            <div key={f.key}>
              <label className="block text-sm font-medium text-gray-700 mb-1">{f.label}</label>
              {f.type === "textarea" ? (
                <textarea
                  placeholder={f.placeholder}
                  required
                  rows={4}
                  value={fields[f.key] ?? ""}
                  onChange={(e) => setFields((p) => ({ ...p, [f.key]: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
                />
              ) : (
                <input
                  type={f.type ?? "text"}
                  placeholder={f.placeholder}
                  required
                  value={fields[f.key] ?? ""}
                  onChange={(e) => setFields((p) => ({ ...p, [f.key]: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              )}
            </div>
          ))}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white font-medium rounded-lg px-4 py-2.5 text-sm transition-colors"
          >
            {loading ? "Connecting…" : "Connect & continue"}
          </button>
        </form>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-900 mb-1">Connect your first integration</h2>
      <p className="text-gray-500 text-sm mb-6">
        Pick the tool your team uses — you can add more later.
      </p>
      <div className="grid grid-cols-1 gap-3 max-w-lg">
        {INTEGRATIONS.map((i) => (
          <button
            key={i.type}
            onClick={() => setSelected(i.type)}
            className="flex items-center justify-between bg-white border border-gray-200 hover:border-brand-400 hover:shadow-sm rounded-xl p-4 text-left transition-all group"
          >
            <div>
              <p className="font-semibold text-gray-900 text-sm group-hover:text-brand-700">{i.label}</p>
              <p className="text-xs text-gray-400 mt-0.5">{i.description}</p>
            </div>
            <ArrowRight className="w-4 h-4 text-gray-300 group-hover:text-brand-500 shrink-0 ml-4" />
          </button>
        ))}
      </div>
    </div>
  );
}

// ── Step 3: Collect & finish ─────────────────────────────────────────────────
function StepCollect({
  integrationType,
  onFinish,
}: {
  integrationType: string;
  onFinish: () => void;
}) {
  const [collecting, setCollecting] = useState(false);
  const [done, setDone] = useState(false);

  const handleCollect = async () => {
    setCollecting(true);
    try {
      await api.triggerCollect(integrationType);
      setDone(true);
    } catch {
      // Still let them proceed
      setDone(true);
    } finally {
      setCollecting(false);
    }
  };

  return (
    <div className="text-center">
      <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6 transition-colors ${done ? "bg-green-50" : "bg-brand-50"}`}>
        {done
          ? <CheckCircle2 className="w-8 h-8 text-green-500" />
          : <Zap className="w-8 h-8 text-brand-600" />
        }
      </div>

      {done ? (
        <>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">You&apos;re all set!</h2>
          <p className="text-gray-500 mb-8 max-w-sm mx-auto">
            Evidence collection has started. Your compliance score will be ready in a few moments.
          </p>
          <button
            onClick={onFinish}
            className="inline-flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white font-medium px-6 py-2.5 rounded-lg transition-colors"
          >
            Go to dashboard <ArrowRight className="w-4 h-4" />
          </button>
        </>
      ) : (
        <>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Run your first collection</h2>
          <p className="text-gray-500 mb-8 max-w-sm mx-auto">
            TraceLayer will pull evidence from <span className="font-medium capitalize">{integrationType.replace("_", " ")}</span> and map it to your compliance controls.
          </p>
          <button
            onClick={handleCollect}
            disabled={collecting}
            className="inline-flex items-center gap-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white font-medium px-6 py-2.5 rounded-lg transition-colors"
          >
            {collecting ? (
              <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Collecting…</>
            ) : (
              <><Zap className="w-4 h-4" /> Collect evidence now</>
            )}
          </button>
          <p className="text-xs text-gray-400 mt-4">
            Collections also run automatically every 24 hours.
          </p>
        </>
      )}
    </div>
  );
}

// ── Main page ────────────────────────────────────────────────────────────────
export default function OnboardingPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [connectedType, setConnectedType] = useState("");

  // Skip onboarding if they already have integrations
  useEffect(() => {
    api.getIntegrations().then((ints) => {
      if (ints.length > 0) router.replace("/dashboard");
    }).catch(() => {});
  }, [router]);

  const handleSkip = () => router.push("/dashboard");

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b border-gray-200 px-8 py-4 flex items-center justify-between">
        <span className="font-bold text-gray-900 text-lg">TraceLayer</span>
        <button
          onClick={handleSkip}
          className="flex items-center gap-1 text-sm text-gray-400 hover:text-gray-600 transition-colors"
        >
          <X className="w-4 h-4" /> Skip setup
        </button>
      </header>

      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-2xl">
          <StepIndicator current={step} />

          <div className="bg-white rounded-2xl border border-gray-200 p-8 shadow-sm">
            {step === 1 && (
              <StepWelcome
                name={user?.email?.split("@")[0] ?? ""}
                onNext={() => setStep(2)}
              />
            )}
            {step === 2 && (
              <StepConnect
                onNext={(type) => { setConnectedType(type); setStep(3); }}
              />
            )}
            {step === 3 && (
              <StepCollect
                integrationType={connectedType}
                onFinish={() => router.push("/dashboard")}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

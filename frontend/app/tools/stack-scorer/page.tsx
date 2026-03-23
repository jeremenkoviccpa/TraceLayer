"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import {
  ArrowLeft, ArrowRight, Activity, CheckCircle2, XCircle,
  AlertCircle, ChevronRight, Layers, Search, BarChart3,
  Shield, Zap, Database, Lock,
} from "lucide-react";
import { ToolEmailGate } from "@/components/tool-email-gate";

// ── Integration catalogue ─────────────────────────────────────────────────────

interface IntegrationDef {
  type: string;
  label: string;
  popular?: boolean;
}

const GROUPS: { label: string; color: string; bg: string; border: string; icon: React.ElementType; items: IntegrationDef[] }[] = [
  {
    label: "Cloud Infrastructure",
    color: "text-orange-600",
    bg: "bg-orange-50",
    border: "border-orange-100",
    icon: Layers,
    items: [
      { type: "aws",          label: "AWS",           popular: true  },
      { type: "gcp",          label: "Google Cloud",  popular: true  },
      { type: "azure",        label: "Azure",         popular: true  },
      { type: "digitalocean", label: "DigitalOcean"                  },
      { type: "heroku",       label: "Heroku"                        },
      { type: "render",       label: "Render"                        },
      { type: "flyio",        label: "Fly.io"                        },
      { type: "netlify",      label: "Netlify"                       },
      { type: "oracle_cloud", label: "Oracle Cloud"                  },
    ],
  },
  {
    label: "Identity & Access",
    color: "text-violet-600",
    bg: "bg-violet-50",
    border: "border-violet-100",
    icon: Lock,
    items: [
      { type: "okta",                    label: "Okta",              popular: true },
      { type: "google_workspace",        label: "Google Workspace",  popular: true },
      { type: "jumpcloud",               label: "JumpCloud"                        },
      { type: "auth0",                   label: "Auth0"                            },
      { type: "onelogin",                label: "OneLogin"                         },
      { type: "ping_identity",           label: "Ping Identity"                    },
      { type: "microsoft_authenticator", label: "Microsoft Authenticator"          },
      { type: "zscaler",                 label: "Zscaler"                          },
    ],
  },
  {
    label: "Code & CI/CD",
    color: "text-gray-700",
    bg: "bg-gray-50",
    border: "border-gray-200",
    icon: Activity,
    items: [
      { type: "github",      label: "GitHub",       popular: true },
      { type: "gitlab",      label: "GitLab",       popular: true },
      { type: "bitbucket",   label: "Bitbucket"                   },
      { type: "jenkins",     label: "Jenkins"                     },
      { type: "circleci",    label: "CircleCI"                    },
      { type: "azure_devops",label: "Azure DevOps"                },
      { type: "argocd",      label: "ArgoCD"                      },
      { type: "kubernetes",  label: "Kubernetes"                  },
    ],
  },
  {
    label: "Security",
    color: "text-rose-600",
    bg: "bg-rose-50",
    border: "border-rose-100",
    icon: Shield,
    items: [
      { type: "snyk",           label: "Snyk",        popular: true },
      { type: "crowdstrike",    label: "CrowdStrike"               },
      { type: "sentinelone",    label: "SentinelOne"               },
      { type: "qualys",         label: "Qualys"                    },
      { type: "tenable",        label: "Tenable"                   },
      { type: "veracode",       label: "Veracode"                  },
      { type: "aquasec",        label: "Aqua Security"             },
      { type: "detectify",      label: "Detectify"                 },
      { type: "kolide",         label: "Kolide"                    },
      { type: "kandji",         label: "Kandji"                    },
    ],
  },
  {
    label: "Monitoring & Alerting",
    color: "text-blue-600",
    bg: "bg-blue-50",
    border: "border-blue-100",
    icon: BarChart3,
    items: [
      { type: "datadog",            label: "Datadog",           popular: true },
      { type: "new_relic",          label: "New Relic"                        },
      { type: "grafana",            label: "Grafana"                          },
      { type: "splunk",             label: "Splunk"                           },
      { type: "elastic",            label: "Elastic"                          },
      { type: "pagerduty",          label: "PagerDuty"                        },
      { type: "opsgenie",           label: "Opsgenie"                         },
      { type: "microsoft_sentinel", label: "Microsoft Sentinel"               },
      { type: "betteruptime",       label: "BetterUptime"                     },
    ],
  },
  {
    label: "Communication",
    color: "text-teal-600",
    bg: "bg-teal-50",
    border: "border-teal-100",
    icon: Activity,
    items: [
      { type: "slack",           label: "Slack",            popular: true },
      { type: "microsoft_teams", label: "Microsoft Teams"                 },
      { type: "zoom",            label: "Zoom"                            },
      { type: "webex",           label: "Webex"                           },
      { type: "intercom",        label: "Intercom"                        },
    ],
  },
  {
    label: "Ticketing & ITSM",
    color: "text-indigo-600",
    bg: "bg-indigo-50",
    border: "border-indigo-100",
    icon: Database,
    items: [
      { type: "jira",        label: "Jira",        popular: true },
      { type: "linear",      label: "Linear"                     },
      { type: "servicenow",  label: "ServiceNow"                 },
      { type: "zendesk",     label: "Zendesk"                    },
      { type: "asana",       label: "Asana"                      },
      { type: "monday",      label: "Monday.com"                 },
      { type: "clickup",     label: "ClickUp"                    },
      { type: "shortcut",    label: "Shortcut"                   },
    ],
  },
  {
    label: "HR & People",
    color: "text-pink-600",
    bg: "bg-pink-50",
    border: "border-pink-100",
    icon: Zap,
    items: [
      { type: "bamboohr",  label: "BambooHR",  popular: true },
      { type: "rippling",  label: "Rippling"                 },
      { type: "workday",   label: "Workday"                  },
      { type: "greenhouse",label: "Greenhouse"               },
      { type: "hibob",     label: "HiBob"                    },
      { type: "personio",  label: "Personio"                  },
      { type: "deel",      label: "Deel"                      },
      { type: "remote",    label: "Remote"                    },
      { type: "checkr",    label: "Checkr"                    },
      { type: "lattice",   label: "Lattice"                   },
    ],
  },
  {
    label: "Secrets & Config",
    color: "text-amber-600",
    bg: "bg-amber-50",
    border: "border-amber-100",
    icon: Lock,
    items: [
      { type: "1password", label: "1Password", popular: true },
      { type: "bitwarden", label: "Bitwarden"               },
      { type: "lastpass",  label: "LastPass"                 },
      { type: "doppler",   label: "Doppler"                  },
    ],
  },
];

// ── Types ─────────────────────────────────────────────────────────────────────

interface FrameworkResult {
  framework: string;
  label: string;
  projected_score: number;
  covered_controls: string[];
  partial_controls: { label: string; covered: string[]; missing: string[] }[];
  missing_controls: { label: string; missing: string[] }[];
}

interface EvidenceItem {
  type: string;
  label: string;
  control: string;
  typical_count: number;
  integration: string;
}

interface DataCategory {
  key: string;
  label: string;
  color: string;
  regulatory_notes: string[];
}

interface SimResult {
  framework_results: FrameworkResult[];
  total_records: number;
  evidence_preview: EvidenceItem[];
  data_categories: DataCategory[];
  integration_count: number;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const CAT_COLOR_MAP: Record<string, string> = {
  purple:  "bg-violet-100 text-violet-700 border-violet-200",
  blue:    "bg-blue-100 text-blue-700 border-blue-200",
  green:   "bg-emerald-100 text-emerald-700 border-emerald-200",
  orange:  "bg-orange-100 text-orange-700 border-orange-200",
  red:     "bg-rose-100 text-rose-700 border-rose-200",
  gray:    "bg-gray-100 text-gray-600 border-gray-200",
  pink:    "bg-pink-100 text-pink-700 border-pink-200",
  yellow:  "bg-yellow-100 text-yellow-700 border-yellow-200",
  teal:    "bg-teal-100 text-teal-700 border-teal-200",
  indigo:  "bg-indigo-100 text-indigo-700 border-indigo-200",
};

function scoreColor(score: number) {
  if (score >= 70) return { bar: "bg-emerald-500", text: "text-emerald-600", ring: "ring-emerald-200" };
  if (score >= 40) return { bar: "bg-amber-400",   text: "text-amber-600",   ring: "ring-amber-200"   };
  return             { bar: "bg-rose-400",    text: "text-rose-600",    ring: "ring-rose-200"    };
}

// ── Score dial ────────────────────────────────────────────────────────────────

function ScoreDial({ score, label }: { score: number; label: string }) {
  const colors = scoreColor(score);
  const circumference = 2 * Math.PI * 36;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className={`relative w-24 h-24 rounded-full ring-4 ${colors.ring}`}>
        <svg className="w-24 h-24 -rotate-90" viewBox="0 0 80 80">
          <circle cx="40" cy="40" r="36" fill="none" stroke="#e5e7eb" strokeWidth="7" />
          <circle
            cx="40" cy="40" r="36" fill="none"
            stroke={score >= 70 ? "#10b981" : score >= 40 ? "#f59e0b" : "#f87171"}
            strokeWidth="7"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: "stroke-dashoffset 1s ease" }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={`text-xl font-black ${colors.text}`}>{score}%</span>
        </div>
      </div>
      <span className="text-sm font-bold text-gray-800">{label}</span>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function StackScorerPage() {
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SimResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [emailCaptured, setEmailCaptured] = useState(false);

  function toggle(type: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  }

  function toggleGroup(items: IntegrationDef[]) {
    const allSelected = items.every((i) => selected.has(i.type));
    setSelected((prev) => {
      const next = new Set(prev);
      items.forEach((i) => (allSelected ? next.delete(i.type) : next.add(i.type)));
      return next;
    });
  }

  async function calculate() {
    if (selected.size === 0) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/v1/public/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ integration_types: Array.from(selected) }),
      });
      if (!res.ok) throw new Error("Simulation failed");
      setResult(await res.json());
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setResult(null);
    setSelected(new Set());
    setSearch("");
    setEmailCaptured(false);
  }

  const filteredGroups = search.trim()
    ? GROUPS.map((g) => ({
        ...g,
        items: g.items.filter((i) => i.label.toLowerCase().includes(search.toLowerCase())),
      })).filter((g) => g.items.length > 0)
    : GROUPS;

  return (
    <div className="min-h-screen bg-[#f7f1e8] font-[family:'Sora',_ui-sans-serif,_system-ui]">

      {/* Nav */}
      <header className="sticky top-0 z-50 bg-[#f7f1e8]/95 backdrop-blur-md border-b border-black/5">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 shrink-0">
            <Image src="/logo-icon.png" alt="TraceLayer" width={28} height={28} className="rounded-lg" />
            <span className="font-extrabold text-base tracking-tight text-gray-900">TraceLayer</span>
          </Link>
          <Link href="/tools" className="hidden md:flex items-center gap-1 text-sm text-gray-500 hover:text-gray-900 font-medium px-3 py-1.5 rounded-lg hover:bg-black/5 transition-all">
            <ArrowLeft className="w-3.5 h-3.5" /> Free Tools
          </Link>
          <div className="flex items-center gap-2">
            <Link href="/login" className="hidden md:block text-sm text-gray-500 hover:text-gray-900 font-medium px-3 py-1.5 rounded-lg hover:bg-black/5 transition-all">
              Sign in
            </Link>
            <Link href="/register" className="text-sm bg-teal-600 hover:bg-teal-700 text-white font-semibold px-4 py-1.5 rounded-lg transition-colors shadow-sm">
              Get started free
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-3xl mx-auto px-6 pt-14 pb-8 text-center">
        <div className="inline-flex items-center gap-2 bg-teal-100 text-teal-700 text-xs font-semibold px-3 py-1.5 rounded-full mb-5 border border-teal-200">
          <Activity className="w-3.5 h-3.5" />
          Simulation · Select your stack · Instant results
        </div>
        <h1 className="text-3xl md:text-4xl font-extrabold text-gray-900 mb-4 leading-tight tracking-tight">
          Compliance Stack Scorer
        </h1>
        <p className="text-gray-500 text-base max-w-xl mx-auto leading-relaxed mb-6">
          Select every tool your team already uses. We'll calculate your projected SOC 2, ISO 27001, and HIPAA readiness score — and show exactly what evidence would be collected automatically.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-4 text-xs text-gray-500">
          {["No signup required", "Based on real evidence mapping", "Instant score projection"].map((t) => (
            <span key={t} className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-teal-500" /> {t}
            </span>
          ))}
        </div>
      </section>

      {/* Tool area */}
      <section className="bg-slate-900 py-12 md:py-16 overflow-hidden relative">
        <div className="absolute -top-32 right-0 w-96 h-96 rounded-full bg-[radial-gradient(circle,rgba(20,184,166,0.12),transparent)] pointer-events-none" />
        <div className="absolute -bottom-20 -left-10 w-80 h-80 rounded-full bg-[radial-gradient(circle,rgba(139,92,246,0.08),transparent)] pointer-events-none" />

        <div className="max-w-5xl mx-auto px-4 sm:px-6 relative">

          {!result ? (
            /* ── Picker ──────────────────────────────────────────────────── */
            <div className="bg-slate-800 rounded-2xl border border-white/10 overflow-hidden">

              {/* Picker header */}
              <div className="px-6 py-5 border-b border-white/10 flex flex-col sm:flex-row sm:items-center gap-4">
                <div className="flex-1">
                  <h2 className="text-white font-extrabold text-lg">Which tools does your team use?</h2>
                  <p className="text-white/50 text-sm mt-0.5">Select everything in your stack — cloud, identity, code, security, communication.</p>
                </div>
                <div className="relative shrink-0">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/30" />
                  <input
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search tools..."
                    className="w-48 bg-slate-700 border border-white/10 text-white text-sm placeholder:text-white/30 rounded-lg pl-8 pr-3 py-2 focus:outline-none focus:ring-1 focus:ring-teal-500"
                  />
                </div>
              </div>

              {/* Integration groups */}
              <div className="px-6 py-6 space-y-8 max-h-[60vh] overflow-y-auto">
                {filteredGroups.map((group) => {
                  const GroupIcon = group.icon;
                  const allGroupSelected = group.items.every((i) => selected.has(i.type));
                  return (
                    <div key={group.label}>
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <GroupIcon className="w-4 h-4 text-white/40" />
                          <span className="text-xs font-bold text-white/50 uppercase tracking-widest">{group.label}</span>
                        </div>
                        <button
                          onClick={() => toggleGroup(group.items)}
                          className="text-xs font-semibold text-teal-400 hover:text-teal-300 transition-colors"
                        >
                          {allGroupSelected ? "Deselect all" : "Select all"}
                        </button>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {group.items.map((item) => {
                          const isSelected = selected.has(item.type);
                          return (
                            <button
                              key={item.type}
                              onClick={() => toggle(item.type)}
                              className={`relative inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                                isSelected
                                  ? "bg-teal-500/20 border-teal-500/50 text-teal-300"
                                  : "bg-white/5 border-white/10 text-white/60 hover:bg-white/10 hover:text-white/80"
                              }`}
                            >
                              {isSelected && <CheckCircle2 className="w-3 h-3 shrink-0" />}
                              {item.label}
                              {item.popular && !isSelected && (
                                <span className="w-1.5 h-1.5 rounded-full bg-teal-500/60 shrink-0" />
                              )}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Sticky footer */}
              <div className="px-6 py-4 border-t border-white/10 bg-slate-900/60 flex items-center justify-between gap-4">
                <div>
                  {selected.size > 0 ? (
                    <p className="text-sm text-white/70">
                      <span className="font-bold text-white">{selected.size}</span> tool{selected.size !== 1 ? "s" : ""} selected
                    </p>
                  ) : (
                    <p className="text-sm text-white/40">Select at least 1 tool to score your stack</p>
                  )}
                </div>
                <button
                  onClick={calculate}
                  disabled={selected.size === 0 || loading}
                  className="inline-flex items-center gap-2 bg-teal-500 hover:bg-teal-400 disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold px-6 py-2.5 rounded-xl transition-colors text-sm"
                >
                  {loading ? (
                    <>
                      <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Calculating...
                    </>
                  ) : (
                    <>Calculate my score <ArrowRight className="w-4 h-4" /></>
                  )}
                </button>
              </div>

              {error && (
                <p className="px-6 py-3 text-sm text-rose-400 bg-rose-500/10 border-t border-rose-500/20">{error}</p>
              )}
            </div>

          ) : result && !emailCaptured ? (
            /* ── Email gate ────────────────────────────────────────────────── */
            <ToolEmailGate
              toolName="compliance-stack-scorer"
              headline={`Your stack scores ${result.framework_results[0]?.projected_score ?? 0}% on ${result.framework_results[0]?.label ?? "SOC 2"}`}
              subline={`${result.integration_count} integration${result.integration_count !== 1 ? "s" : ""} · ~${result.total_records.toLocaleString()} evidence records / day`}
              teasers={result.framework_results.map((fw) => ({
                label: fw.label,
                value: `${fw.projected_score}%`,
                valueColor:
                  fw.projected_score >= 70
                    ? "text-emerald-600"
                    : fw.projected_score >= 40
                    ? "text-amber-600"
                    : "text-rose-600",
              }))}
              onUnlocked={() => setEmailCaptured(true)}
            />
          ) : (
            /* ── Results ──────────────────────────────────────────────────── */
            <div className="space-y-5">

              {/* Header */}
              <div className="text-center mb-8">
                <p className="text-teal-400 text-xs font-bold uppercase tracking-widest mb-2">Based on {result.integration_count} integration{result.integration_count !== 1 ? "s" : ""}</p>
                <h2 className="text-2xl md:text-3xl font-extrabold text-white mb-2">Your projected compliance score</h2>
                <p className="text-white/50 text-sm">
                  ~{result.total_records.toLocaleString()} evidence records collected automatically every 24h
                </p>
              </div>

              {/* Framework dials */}
              <div className="bg-slate-800 rounded-2xl border border-white/10 p-6">
                <div className="flex flex-wrap justify-around gap-8">
                  {result.framework_results.map((fw) => (
                    <ScoreDial key={fw.framework} score={fw.projected_score} label={fw.label} />
                  ))}
                </div>
              </div>

              {/* Framework breakdown */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {result.framework_results.map((fw) => {
                  const colors = scoreColor(fw.projected_score);
                  return (
                    <div key={fw.framework} className="bg-slate-800 rounded-2xl border border-white/10 p-5">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-white font-bold text-sm">{fw.label}</span>
                        <span className={`text-sm font-black ${colors.text}`}>{fw.projected_score}%</span>
                      </div>
                      <div className="w-full h-2 bg-white/10 rounded-full mb-4">
                        <div
                          className={`h-2 rounded-full transition-all duration-1000 ${colors.bar}`}
                          style={{ width: `${fw.projected_score}%` }}
                        />
                      </div>

                      {/* Covered */}
                      {fw.covered_controls.length > 0 && (
                        <div className="space-y-1.5 mb-2">
                          {fw.covered_controls.map((c) => (
                            <div key={c} className="flex items-center gap-2 text-xs text-emerald-400">
                              <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                              <span>{c}</span>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Partial */}
                      {fw.partial_controls.map((c) => (
                        <div key={c.label} className="flex items-start gap-2 text-xs text-amber-400 mb-1.5">
                          <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                          <div>
                            <span className="font-semibold">{c.label}</span>
                            <span className="text-white/30 ml-1">({c.missing.length} type{c.missing.length !== 1 ? "s" : ""} missing)</span>
                          </div>
                        </div>
                      ))}

                      {/* Missing */}
                      {fw.missing_controls.map((c) => (
                        <div key={c.label} className="flex items-start gap-2 text-xs text-rose-400 mb-1.5">
                          <XCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                          <span className="font-semibold">{c.label}</span>
                        </div>
                      ))}
                    </div>
                  );
                })}
              </div>

              {/* Evidence preview */}
              {result.evidence_preview.length > 0 && (
                <div className="bg-slate-800 rounded-2xl border border-white/10 p-5">
                  <h3 className="text-white font-bold text-sm mb-4 flex items-center gap-2">
                    <Database className="w-4 h-4 text-teal-400" />
                    Evidence collected automatically
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {result.evidence_preview.slice(0, 12).map((ev) => (
                      <div key={ev.type} className="flex items-center justify-between bg-white/5 rounded-lg px-3 py-2">
                        <div className="min-w-0">
                          <p className="text-xs font-semibold text-white/80 truncate">{ev.label}</p>
                          <p className="text-[10px] text-white/30">{ev.integration}</p>
                        </div>
                        <span className="text-xs font-bold text-teal-400 shrink-0 ml-2">
                          ~{ev.typical_count.toLocaleString()}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Data categories */}
              {result.data_categories.length > 0 && (
                <div className="bg-slate-800 rounded-2xl border border-white/10 p-5">
                  <h3 className="text-white font-bold text-sm mb-3 flex items-center gap-2">
                    <Shield className="w-4 h-4 text-violet-400" />
                    Data categories in scope
                  </h3>
                  <div className="flex flex-wrap gap-2 mb-4">
                    {result.data_categories.map((cat) => (
                      <span
                        key={cat.key}
                        className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full border ${
                          CAT_COLOR_MAP[cat.color] ?? "bg-gray-100 text-gray-600 border-gray-200"
                        }`}
                      >
                        {cat.label}
                      </span>
                    ))}
                  </div>
                  <div className="space-y-2">
                    {result.data_categories.flatMap((cat) =>
                      cat.regulatory_notes.map((note) => (
                        <div key={note} className="flex items-start gap-2 text-xs text-white/40">
                          <ChevronRight className="w-3.5 h-3.5 shrink-0 mt-0.5 text-white/20" />
                          {note}
                        </div>
                      ))
                    ).slice(0, 6)}
                  </div>
                </div>
              )}

              {/* CTA */}
              <div className="bg-gradient-to-r from-teal-600 to-emerald-600 rounded-2xl p-6 md:p-8 text-center">
                <h3 className="text-white font-extrabold text-xl mb-2">Get this for real — in 5 minutes</h3>
                <p className="text-white/80 text-sm mb-6 max-w-md mx-auto">
                  Connect these tools to TraceLayer and evidence starts flowing automatically. Your real score updates every 24 hours.
                </p>
                <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
                  <Link
                    href="/register"
                    className="inline-flex items-center gap-2 bg-white hover:bg-white/90 text-teal-700 font-bold px-7 py-3 rounded-xl transition-colors text-sm shadow-md"
                  >
                    Start free — no credit card <ArrowRight className="w-4 h-4" />
                  </Link>
                  <button
                    onClick={reset}
                    className="text-white/60 hover:text-white text-sm font-medium transition-colors"
                  >
                    ← Try a different stack
                  </button>
                </div>
              </div>

            </div>
          )}
        </div>
      </section>

      {/* What this is */}
      <section className="py-14 bg-[#f7f1e8]">
        <div className="max-w-4xl mx-auto px-6">
          <div className="text-center mb-10">
            <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">How it works</p>
            <h2 className="text-2xl font-extrabold text-gray-900">Based on real evidence mapping — not guesswork</h2>
            <p className="text-gray-500 text-sm mt-2 max-w-lg mx-auto">
              This tool uses the exact same evidence mapping engine TraceLayer uses in production. When you connect a tool for real, you'll see numbers like these.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
            {[
              {
                icon: Activity,
                color: "text-teal-600",
                bg: "bg-teal-50 border-teal-100",
                title: "Real control mapping",
                desc: "Every integration is mapped to the specific SOC 2, ISO 27001, and HIPAA controls its evidence satisfies — the same way auditors evaluate it.",
              },
              {
                icon: Database,
                color: "text-violet-600",
                bg: "bg-violet-50 border-violet-100",
                title: "Accurate evidence counts",
                desc: "Typical record counts are based on real customer data — AWS averages 500 CloudTrail events, GitHub averages 35 repositories, and so on.",
              },
              {
                icon: Shield,
                color: "text-orange-500",
                bg: "bg-orange-50 border-orange-100",
                title: "Gap analysis is real",
                desc: "Missing controls shown here are actual gaps your auditor would flag. The score goes up when you connect tools that cover those controls.",
              },
            ].map((card) => {
              const Icon = card.icon;
              return (
                <div key={card.title} className={`rounded-2xl border p-6 ${card.bg}`}>
                  <Icon className={`w-6 h-6 mb-3 ${card.color}`} />
                  <h3 className="font-extrabold text-gray-900 text-sm mb-2">{card.title}</h3>
                  <p className="text-xs text-gray-500 leading-relaxed">{card.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="bg-teal-600 py-12 md:py-16">
        <div className="max-w-2xl mx-auto px-6 text-center">
          <p className="text-xs font-bold text-white/60 uppercase tracking-widest mb-3">Ready to make it real?</p>
          <h2 className="text-2xl md:text-3xl font-extrabold text-white mb-3 leading-tight">
            Connect your stack. Evidence flows in minutes.
          </h2>
          <p className="text-white/75 text-sm mb-7 max-w-md mx-auto leading-relaxed">
            TraceLayer connects to the tools you selected, collects evidence automatically every 24 hours, and shows your live compliance score.
          </p>
          <Link
            href="/register"
            className="inline-flex items-center gap-2 bg-white hover:bg-white/90 text-teal-700 font-bold px-8 py-3.5 rounded-xl transition-colors text-sm"
          >
            Get started free <ArrowRight className="w-4 h-4" />
          </Link>
          <p className="text-white/50 text-xs mt-3">Free to start · No credit card · Setup in 5 minutes</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-black/5 py-8 bg-[#f7f1e8]">
        <div className="max-w-6xl mx-auto px-6 flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-2.5">
            <Image src="/logo-icon.png" alt="TraceLayer" width={24} height={24} className="rounded-md" />
            <span className="font-extrabold text-sm text-gray-900">TraceLayer</span>
          </div>
          <div className="flex items-center gap-6 text-xs text-gray-400">
            <Link href="/tools" className="hover:text-gray-700 transition-colors">Free Tools</Link>
            <Link href="/#pricing" className="hover:text-gray-700 transition-colors">Pricing</Link>
            <Link href="/login" className="hover:text-gray-700 transition-colors">Sign in</Link>
            <Link href="/register" className="hover:text-gray-700 transition-colors">Get started</Link>
          </div>
          <span className="text-xs text-gray-400">© {new Date().getFullYear()} TraceLayer</span>
        </div>
      </footer>

      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&display=swap');
        html { scroll-behavior: smooth; }
      `}</style>
    </div>
  );
}

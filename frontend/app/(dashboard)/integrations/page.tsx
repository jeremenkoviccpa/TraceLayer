"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { openPaddleCheckout } from "@/lib/paddle";
import type { BillingInfo, Integration } from "@/lib/types";
import { CheckCircle2, AlertCircle, Clock, RefreshCw, Trash2, Plus, X, Zap, Lock, Search, BookOpen, ExternalLink, ChevronDown, ChevronUp, Shield } from "lucide-react";

const FREE_LIMIT = 3;

// ── Compliance checklists ──────────────────────────────────────────────────────
type ChecklistArea = { area: string; control: string; integrations: string[]; note: string };
type Checklist = { label: string; color: string; areas: ChecklistArea[] };

const CHECKLISTS: Record<string, Checklist> = {
  soc2: {
    label: "SOC 2", color: "blue",
    areas: [
      { area: "Identity & Access",     control: "CC6.1–CC6.3", integrations: ["okta","google_workspace","azure_ad","1password"],    note: "Prove MFA is enforced and access is reviewed" },
      { area: "Endpoint Security",     control: "CC6.8",        integrations: ["jamf","kandji","kolide"],                           note: "Device encryption, MDM enrollment, patch status" },
      { area: "Source Control",        control: "CC8.1",        integrations: ["github","gitlab","bitbucket"],                      note: "Branch protection, code reviews, no direct pushes to main" },
      { area: "Vulnerability Mgmt",   control: "CC7.1",        integrations: ["snyk","tenable","crowdstrike","sentinelone"],        note: "Continuous scanning and remediation tracking" },
      { area: "Monitoring & Alerting", control: "CC7.2",        integrations: ["datadog","new_relic","pagerduty","sentry"],         note: "Alert policies and incident response records" },
      { area: "Cloud Infrastructure",  control: "CC6.6",        integrations: ["aws","google_cloud","cloudflare","wiz"],            note: "IAM policies, audit logs, network security" },
      { area: "HR & People",           control: "CC1.4",        integrations: ["bamboohr","rippling"],                             note: "Security training, offboarding, org chart" },
      { area: "Change Management",     control: "CC8.1",        integrations: ["jira","linear","servicenow"],                      note: "Change tickets and approval workflows" },
    ],
  },
  iso27001: {
    label: "ISO 27001", color: "emerald",
    areas: [
      { area: "Access Control",        control: "A.9",  integrations: ["okta","google_workspace","azure_ad","aws"],     note: "Identity management and least-privilege access" },
      { area: "Cryptography",          control: "A.10", integrations: ["aws","google_cloud","vault"],                   note: "Encryption at rest and in transit" },
      { area: "Operations Security",   control: "A.12", integrations: ["datadog","cloudflare","pagerduty","sentry"],    note: "Monitoring, logging, and capacity management" },
      { area: "Secure Development",    control: "A.14", integrations: ["github","gitlab","snyk"],                       note: "Secure SDLC and vulnerability scanning" },
      { area: "Supplier Relationships",control: "A.15", integrations: ["jira","servicenow"],                           note: "Third-party access and change control" },
      { area: "HR Security",           control: "A.7",  integrations: ["bamboohr","rippling"],                         note: "Security training and lifecycle management" },
    ],
  },
  gdpr: {
    label: "GDPR", color: "purple",
    areas: [
      { area: "Security of Processing", control: "Art. 32", integrations: ["aws","google_cloud","cloudflare"],         note: "Encryption and access controls for personal data" },
      { area: "Privacy by Design",      control: "Art. 25", integrations: ["github","gitlab","snyk"],                  note: "Privacy built into development practices" },
      { area: "Data Breach Detection",  control: "Art. 33", integrations: ["datadog","sentry","crowdstrike"],           note: "Detect and report breaches within 72 hours" },
      { area: "Workforce Controls",     control: "Art. 29", integrations: ["bamboohr","rippling","okta"],              note: "Staff training and authorised access only" },
    ],
  },
  hipaa: {
    label: "HIPAA", color: "rose",
    areas: [
      { area: "Access Controls",        control: "§164.312(a)", integrations: ["okta","google_workspace","aws"],        note: "Unique user IDs, auto-logoff, encryption" },
      { area: "Audit Controls",         control: "§164.312(b)", integrations: ["aws","datadog","cloudflare"],           note: "Hardware, software, and network audit logs" },
      { area: "Risk Management",        control: "§164.308(a)", integrations: ["snyk","tenable","crowdstrike"],         note: "Ongoing vulnerability management and risk analysis" },
      { area: "Workforce Security",     control: "§164.308(a)", integrations: ["bamboohr","jamf","kandji"],             note: "Training completion and device security" },
    ],
  },
};

const CHECKLIST_COLORS: Record<string, { tab: string; badge: string; check: string; bar: string }> = {
  blue:    { tab: "bg-blue-600 text-white",    badge: "bg-blue-50 text-blue-700 border-blue-100",    check: "text-blue-500",    bar: "bg-blue-500" },
  emerald: { tab: "bg-emerald-600 text-white", badge: "bg-emerald-50 text-emerald-700 border-emerald-100", check: "text-emerald-500", bar: "bg-emerald-500" },
  purple:  { tab: "bg-purple-600 text-white",  badge: "bg-purple-50 text-purple-700 border-purple-100", check: "text-purple-500",  bar: "bg-purple-500" },
  rose:    { tab: "bg-rose-600 text-white",    badge: "bg-rose-50 text-rose-700 border-rose-100",    check: "text-rose-500",    bar: "bg-rose-500" },
};

function ComplianceChecklist({ connectedTypes }: { connectedTypes: string[] }) {
  const [framework, setFramework] = useState("soc2");
  const [open, setOpen] = useState(false);
  const cl = CHECKLISTS[framework];
  const colors = CHECKLIST_COLORS[cl.color];

  const covered = cl.areas.filter((a) => a.integrations.some((t) => connectedTypes.includes(t)));
  const pct = cl.areas.length ? Math.round((covered.length / cl.areas.length) * 100) : 0;

  return (
    <div className="bg-white border border-gray-100 shadow-card rounded-2xl mb-6 overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-5 py-3.5 hover:bg-gray-50/60 transition-colors"
      >
        <div className="flex items-center gap-2.5">
          <Shield className="w-4 h-4 text-brand-600 shrink-0" />
          <span className="text-sm font-semibold text-gray-800">Compliance setup guide</span>
          <span className="text-xs text-gray-400">— which integrations you need per framework</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-gray-500">{covered.length}/{cl.areas.length} areas covered</span>
          {open ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
        </div>
      </button>

      {open && (
        <div className="px-5 pb-5 border-t border-gray-50">
          {/* Framework tabs */}
          <div className="flex gap-1.5 mt-4 mb-4 flex-wrap">
            {Object.entries(CHECKLISTS).map(([key, val]) => (
              <button
                key={key}
                onClick={() => setFramework(key)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors ${
                  framework === key
                    ? CHECKLIST_COLORS[val.color].tab
                    : "bg-gray-100 text-gray-500 hover:bg-gray-200"
                }`}
              >
                {val.label}
              </button>
            ))}
          </div>

          {/* Progress bar */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-gray-500">{cl.label} coverage</span>
              <span className="text-xs font-semibold text-gray-700">{pct}%</span>
            </div>
            <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div className={`h-full rounded-full transition-all duration-500 ${colors.bar}`} style={{ width: `${pct}%` }} />
            </div>
          </div>

          {/* Areas */}
          <div className="space-y-2">
            {cl.areas.map((area) => {
              const isCovered = area.integrations.some((t) => connectedTypes.includes(t));
              const connectedHere = area.integrations.filter((t) => connectedTypes.includes(t));
              return (
                <div key={area.area} className={`rounded-xl border px-4 py-3 flex items-start gap-3 ${isCovered ? "bg-gray-50/60 border-gray-100" : "bg-white border-gray-100"}`}>
                  <div className={`mt-0.5 shrink-0 ${isCovered ? colors.check : "text-gray-300"}`}>
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`text-xs font-semibold ${isCovered ? "text-gray-700" : "text-gray-600"}`}>{area.area}</span>
                      <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${colors.badge}`}>{area.control}</span>
                      {isCovered && <span className="text-[10px] text-emerald-600 font-semibold">✓ covered by {connectedHere.join(", ")}</span>}
                    </div>
                    <p className="text-[11px] text-gray-400 mt-0.5">{area.note}</p>
                    {!isCovered && (
                      <div className="flex gap-1 mt-1.5 flex-wrap">
                        {area.integrations.slice(0, 4).map((t) => (
                          <span key={t} className="text-[10px] bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded font-medium">{t}</span>
                        ))}
                        {area.integrations.length > 4 && (
                          <span className="text-[10px] text-gray-400">+{area.integrations.length - 4} more</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

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
  "1password": { bg: "#1A6CE6", label: "1P" },
  cloudflare:  { bg: "#F48120", label: "CF" },
  crowdstrike: { bg: "#E01A22", label: "CR" },
  jamf:        { bg: "#007DC3", label: "JA" },
  vercel: {
    bg: "#000000", label: "VC",
    svg: (s) => <path d={`M${s*0.5} ${s*0.25} L${s*0.82} ${s*0.75} L${s*0.18} ${s*0.75} Z`} fill="white"/>,
  },
  terraform_cloud: { bg: "#7B42BC", label: "TF" },
  snyk:        { bg: "#4C4A73", label: "SY" },
  wiz:         { bg: "#00B3E3", label: "WZ" },
  sentinelone: { bg: "#7F2BDB", label: "S1" },
  kandji:      { bg: "#0066CC", label: "KN" },
  duo:         { bg: "#6DBE4E", label: "DU" },
  splunk:      { bg: "#1A1A1A", label: "SP" },
  servicenow:  { bg: "#62D84E", label: "NOW" },
  kolide:      { bg: "#5C7CFF", label: "KL" },
  hackerone:   { bg: "#494649", label: "H1" },
  confluence:  { bg: "#1868DB", label: "CO" },
  new_relic:   { bg: "#008C99", label: "NR" },
  tenable:     { bg: "#00A1CB", label: "TE" },
  vault:       { bg: "#FFD814", label: "V",
    svg: (s) => <text x={s/2} y={s/2} textAnchor="middle" dominantBaseline="central" fill="#1C1C1C" fontFamily="system-ui" fontWeight="800" fontSize={s*0.42}>V</text>,
  },
  // ── New batch ──────────────────────────────────────────────────────────────
  jumpcloud:    { bg: "#0073E6", label: "JC" },
  bitbucket:    { bg: "#0052CC", label: "BB",
    svg: (s) => (
      <>
        <rect width={s} height={s} rx={Math.round(s*0.25)} fill="#0052CC"/>
        <path d={`M${s*0.15} ${s*0.28} L${s*0.38} ${s*0.72} L${s*0.62} ${s*0.72} L${s*0.85} ${s*0.28} Z`} fill="white" opacity="0.9"/>
        <path d={`M${s*0.38} ${s*0.72} L${s*0.44} ${s*0.54} L${s*0.56} ${s*0.54} L${s*0.62} ${s*0.72} Z`} fill="#0052CC"/>
      </>
    ),
  },
  zendesk:      { bg: "#03363D", label: "ZD" },
  kubernetes:   { bg: "#326CE5", label: "K8S",
    svg: (s) => (
      <>
        <circle cx={s/2} cy={s/2} r={s*0.3} stroke="white" strokeWidth={s*0.08} fill="none"/>
        <line x1={s/2} y1={s*0.2} x2={s/2} y2={s*0.8} stroke="white" strokeWidth={s*0.06}/>
        <line x1={s*0.2} y1={s/2} x2={s*0.8} y2={s/2} stroke="white" strokeWidth={s*0.06}/>
        <line x1={s*0.29} y1={s*0.29} x2={s*0.71} y2={s*0.71} stroke="white" strokeWidth={s*0.06}/>
        <line x1={s*0.71} y1={s*0.29} x2={s*0.29} y2={s*0.71} stroke="white" strokeWidth={s*0.06}/>
      </>
    ),
  },
  circleci:     { bg: "#343434", label: "CI",
    svg: (s) => (
      <>
        <circle cx={s/2} cy={s/2} r={s*0.3} stroke="#F5A623" strokeWidth={s*0.08} fill="none"/>
        <circle cx={s/2} cy={s/2} r={s*0.1} fill="#F5A623"/>
      </>
    ),
  },
  qualys:       { bg: "#E2002A", label: "QL" },
  // ── Coming soon ────────────────────────────────────────────────────────────
  workday:      { bg: "#FF6D3B", label: "WD" },
  gusto:        { bg: "#F45D48", label: "GU" },
  jenkins:      { bg: "#D33833", label: "JK" },
  elastic:      { bg: "#005571", label: "EL" },
  dynatrace:    { bg: "#1496FF", label: "DYN" },
  sumo_logic:   { bg: "#000099", label: "SL" },
  lacework:     { bg: "#FF5F00", label: "LW" },
  carbon_black: { bg: "#101820", label: "CB" },
  rapid7:       { bg: "#E8451C", label: "R7" },
  prisma_cloud: { bg: "#00C0E8", label: "PC" },
  azure_devops: { bg: "#0078D4", label: "ADO" },
  freshdesk:    { bg: "#25C16F", label: "FD" },
  argocd:       { bg: "#EF7B4D", label: "ARGO" },
  // ── New batch ──────────────────────────────────────────────────────────────
  azure:        { bg: "#0078D4", label: "AZ",
    svg: (s) => (
      <>
        <text x={s/2} y={s*0.54} textAnchor="middle" dominantBaseline="central" fill="white"
          fontFamily="system-ui" fontWeight="800" fontSize={s*0.36}>Az</text>
      </>
    ),
  },
  digitalocean: { bg: "#0080FF", label: "DO",
    svg: (s) => (
      <>
        <circle cx={s/2} cy={s/2} r={s*0.27} fill="white"/>
        <circle cx={s/2} cy={s/2} r={s*0.16} fill="#0080FF"/>
        <rect x={s*0.23} y={s*0.63} width={s*0.16} height={s*0.08} rx={2} fill="white"/>
        <rect x={s*0.23} y={s*0.74} width={s*0.11} height={s*0.08} rx={2} fill="white"/>
      </>
    ),
  },
  heroku:       { bg: "#430098", label: "HK" },
  tailscale:    { bg: "#242424", label: "TS",
    svg: (s) => (
      <>
        <circle cx={s*0.5} cy={s*0.28} r={s*0.1} fill="white"/>
        <circle cx={s*0.28} cy={s*0.5} r={s*0.1} fill="white" opacity={0.6}/>
        <circle cx={s*0.72} cy={s*0.5} r={s*0.1} fill="white" opacity={0.6}/>
        <circle cx={s*0.28} cy={s*0.72} r={s*0.1} fill="white" opacity={0.35}/>
        <circle cx={s*0.72} cy={s*0.72} r={s*0.1} fill="white" opacity={0.35}/>
        <circle cx={s*0.5} cy={s*0.72} r={s*0.1} fill="white" opacity={0.35}/>
      </>
    ),
  },
  bitwarden:    { bg: "#175DDC", label: "BW",
    svg: (s) => (
      <path d={`M${s/2} ${s*0.22} L${s*0.78} ${s*0.32} L${s*0.78} ${s*0.58} Q${s*0.78} ${s*0.78} ${s/2} ${s*0.82} Q${s*0.22} ${s*0.78} ${s*0.22} ${s*0.58} L${s*0.22} ${s*0.32} Z`}
        fill="white"/>
    ),
  },
  lastpass:     { bg: "#CC2028", label: "LP" },
  asana:        { bg: "#F06A6A", label: "AS",
    svg: (s) => (
      <>
        <circle cx={s/2}      cy={s*0.38} r={s*0.16} fill="white"/>
        <circle cx={s*0.3}    cy={s*0.62} r={s*0.16} fill="white" opacity={0.75}/>
        <circle cx={s*0.7}    cy={s*0.62} r={s*0.16} fill="white" opacity={0.75}/>
      </>
    ),
  },
  monday:       { bg: "#FF3D57", label: "MN" },
  shortcut:     { bg: "#573BE8", label: "SC" },
  zoom:         { bg: "#2D8CFF", label: "ZM",
    svg: (s) => (
      <>
        <rect x={s*0.15} y={s*0.32} width={s*0.5} height={s*0.36} rx={s*0.07} fill="white"/>
        <path d={`M${s*0.68} ${s*0.4} L${s*0.85} ${s*0.3} L${s*0.85} ${s*0.7} L${s*0.68} ${s*0.6} Z`} fill="white"/>
      </>
    ),
  },
  intercom:     { bg: "#1F8FFF", label: "IC" },
  detectify:    { bg: "#6B3DF3", label: "DT" },
  nightfall:    { bg: "#0B1B35", label: "NF" },
  checkr:       { bg: "#0BBA72", label: "CK" },
  lattice:      { bg: "#5F2EEA", label: "LA" },
  trainual:     { bg: "#1B94E0", label: "TN" },
  greenhouse:   { bg: "#24A47F", label: "GH" },
  secureframe:  { bg: "#0070F3", label: "SF" },
  drata:        { bg: "#4B48ED", label: "DR" },
  opsgenie:     { bg: "#0052CC", label: "OG" },
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
  core?: boolean;
  fields?: { key: string; label: string; placeholder: string; type?: string; hint?: string }[];
};

type IntegrationGroup = { title: string; integrations: IntegrationDef[] };

const INTEGRATION_GROUPS: IntegrationGroup[] = [
  {
    title: "Identity & Access",
    integrations: [
      {
        type: "google_workspace", label: "Google Workspace", core: true,
        description: "Collect users, admin accounts, and groups via Admin SDK",
        fields: [
          { key: "admin_email", label: "Admin Email", placeholder: "admin@yourcompany.com" },
          { key: "service_account_json", label: "Service Account JSON", placeholder: '{"type":"service_account",...}', type: "textarea" },
        ],
      },
      {
        type: "okta", label: "Okta", core: true,
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
        type: "1password", label: "1Password",
        description: "Collect vault access policies, team members, and MFA enforcement status for CC6.1 evidence",
        fields: [
          { key: "service_account_token", label: "Service Account Token", placeholder: "ops_••••••••", type: "password", hint: "Starts with ops_" },
        ],
      },
      {
        type: "rippling", label: "Rippling",
        description: "Sync employee lifecycle events and offboarding for access reviews",
        fields: [
          { key: "api_key", label: "API Key", placeholder: "••••••••••••", type: "password" },
        ],
      },
      {
        type: "duo", label: "Duo Security",
        description: "Collect MFA enrollment rates, authentication policies, and device trust settings for CC6.1 evidence",
        fields: [
          { key: "integration_key", label: "Integration Key", placeholder: "DIXXXXXXXXXXXXXXXXXX" },
          { key: "secret_key", label: "Secret Key", placeholder: "••••••••••••", type: "password" },
          { key: "api_hostname", label: "API Hostname", placeholder: "api-xxxxxxxx.duosecurity.com" },
        ],
      },
      {
        type: "jumpcloud", label: "JumpCloud",
        description: "Collect users, user groups, device compliance, and access policies from JumpCloud directory for CC6.1 evidence",
        fields: [
          { key: "api_key", label: "API Key", placeholder: "••••••••••••", type: "password", hint: "Admin → API Settings → API Key" },
        ],
      },
      {
        type: "tailscale", label: "Tailscale",
        description: "Collect device inventory, ACL policies, and user access for zero-trust network access evidence",
        fields: [
          { key: "api_key", label: "API Key", placeholder: "tskey-api-••••••••", type: "password", hint: "Tailscale Admin → Settings → Keys → Generate API Key" },
          { key: "tailnet", label: "Tailnet", placeholder: "mycompany.com", hint: "Your organization's tailnet name from the admin console" },
        ],
      },
      {
        type: "bitwarden", label: "Bitwarden",
        description: "Collect organization members, collection access policies, and MFA enforcement for password management evidence",
        fields: [
          { key: "client_id", label: "Client ID", placeholder: "organization.••••••••" },
          { key: "client_secret", label: "Client Secret", placeholder: "••••••••••••", type: "password", hint: "Bitwarden Admin → Organization → API Key" },
        ],
      },
      {
        type: "lastpass", label: "LastPass",
        description: "Collect team members, shared folder policies, MFA requirements, and security dashboard scores",
        fields: [
          { key: "cid", label: "Account Number (CID)", placeholder: "1234567" },
          { key: "provhash", label: "Provisioning Hash", placeholder: "••••••••••••", type: "password", hint: "Admin Console → Advanced → Enterprise API" },
        ],
      },
    ],
  },
  {
    title: "Cloud Infrastructure",
    integrations: [
      {
        type: "aws", label: "Amazon Web Services", core: true,
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
        fields: [
          { key: "service_account_json", label: "Service Account JSON", placeholder: '{"type":"service_account",...}', type: "textarea" },
          { key: "project_id", label: "Project ID", placeholder: "my-gcp-project-123" },
        ],
      },
      {
        type: "vercel", label: "Vercel",
        description: "Collect deployment records, environment variable access, and team member permissions",
        fields: [
          { key: "api_token", label: "API Token", placeholder: "••••••••••••", type: "password" },
          { key: "team_id", label: "Team ID (optional)", placeholder: "team_••••••••" },
        ],
      },
      {
        type: "terraform_cloud", label: "Terraform Cloud",
        description: "Collect workspace runs, state changes, and team access for change management evidence",
        fields: [
          { key: "api_token", label: "API Token", placeholder: "••••••••••••", type: "password" },
          { key: "org_name", label: "Organization Name", placeholder: "my-org" },
        ],
      },
      {
        type: "wiz", label: "Wiz",
        description: "Pull cloud security posture findings, misconfigurations, and risk inventory for continuous evidence",
        fields: [
          { key: "client_id", label: "Client ID", placeholder: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" },
          { key: "client_secret", label: "Client Secret", placeholder: "••••••••••••", type: "password" },
          { key: "api_endpoint", label: "API Endpoint", placeholder: "https://api.us1.app.wiz.io/graphql" },
        ],
      },
      {
        type: "azure", label: "Microsoft Azure",
        description: "Collect resource inventory, RBAC role assignments, Key Vault policies, activity logs, and storage access controls",
        fields: [
          { key: "tenant_id", label: "Tenant ID", placeholder: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" },
          { key: "client_id", label: "Client ID", placeholder: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" },
          { key: "client_secret", label: "Client Secret", placeholder: "••••••••••••", type: "password" },
          { key: "subscription_id", label: "Subscription ID", placeholder: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" },
        ],
      },
      {
        type: "digitalocean", label: "DigitalOcean",
        description: "Collect Droplets, Spaces, Databases, firewall rules, and team member access for infrastructure evidence",
        fields: [
          { key: "api_token", label: "Personal Access Token", placeholder: "dop_v1_••••••••", type: "password", hint: "Starts with dop_v1_ — DigitalOcean → API → Generate New Token (read scope)" },
        ],
      },
      {
        type: "heroku", label: "Heroku",
        description: "Collect app inventory, collaborator access, config var encryption, and release audit trail",
        fields: [
          { key: "api_key", label: "API Key", placeholder: "••••••••-••••-••••-••••-••••••••••••", type: "password", hint: "Heroku Dashboard → Account Settings → API Key" },
        ],
      },
    ],
  },
  {
    title: "Source Control",
    integrations: [
      {
        type: "github", label: "GitHub", core: true,
        description: "Collect repositories, members, admin users, and branch protection rules",
        fields: [
          { key: "token", label: "Personal Access Token", placeholder: "ghp_••••••••", type: "password", hint: "Starts with ghp_ or github_pat_" },
          { key: "org", label: "Organization or Username", placeholder: "my-org or your-github-username", hint: "Works with both GitHub orgs and personal accounts" },
        ],
      },
      {
        type: "gitlab", label: "GitLab", core: true,
        description: "Collect projects, members, and merge request approval settings",
        fields: [
          { key: "token", label: "Personal Access Token", placeholder: "glpat-••••••••", type: "password", hint: "Starts with glpat-" },
          { key: "domain", label: "GitLab Domain", placeholder: "gitlab.com" },
        ],
      },
      {
        type: "bitbucket", label: "Bitbucket",
        description: "Collect repositories, branch protection rules, and workspace members for change management evidence",
        fields: [
          { key: "username", label: "Username", placeholder: "your-username" },
          { key: "app_password", label: "App Password", placeholder: "••••••••••••", type: "password", hint: "Create in Bitbucket → Personal Settings → App passwords" },
          { key: "workspace", label: "Workspace", placeholder: "my-workspace", hint: "The workspace slug from your Bitbucket URL" },
        ],
      },
    ],
  },
  {
    title: "Project Management",
    integrations: [
      {
        type: "jira", label: "Jira", core: true,
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
        fields: [
          { key: "api_key", label: "API Key", placeholder: "lin_api_••••••••", type: "password", hint: "Starts with lin_api_" },
        ],
      },
      {
        type: "notion", label: "Notion",
        description: "Sync policy documents and runbooks as compliance evidence",
        fields: [
          { key: "api_key", label: "Integration Token", placeholder: "secret_••••••••", type: "password", hint: "Starts with secret_" },
        ],
      },
      {
        type: "confluence", label: "Confluence",
        description: "Collect policy pages, runbooks, and space permissions as documentation evidence",
        fields: [
          { key: "domain", label: "Confluence Domain", placeholder: "mycompany.atlassian.net" },
          { key: "email", label: "Admin Email", placeholder: "admin@mycompany.com" },
          { key: "api_token", label: "API Token", placeholder: "••••••••••••", type: "password" },
        ],
      },
      {
        type: "servicenow", label: "ServiceNow",
        description: "Collect ITSM tickets, change requests, and incident records for ITIL-aligned evidence",
        fields: [
          { key: "instance", label: "Instance Name", placeholder: "mycompany", hint: "The part before .service-now.com" },
          { key: "username", label: "Username", placeholder: "admin" },
          { key: "password", label: "Password", placeholder: "••••••••••••", type: "password" },
        ],
      },
      {
        type: "asana", label: "Asana",
        description: "Collect projects, tasks, and team member access for change management and workflow evidence",
        fields: [
          { key: "access_token", label: "Personal Access Token", placeholder: "1/••••••••••••", type: "password", hint: "Asana → My Profile → Apps → Manage Developer Apps → New Access Token" },
          { key: "workspace_gid", label: "Workspace GID (optional)", placeholder: "1234567890", hint: "Found in your Asana workspace URL" },
        ],
      },
      {
        type: "monday", label: "Monday.com",
        description: "Collect boards, users, and workspace permissions for project governance evidence",
        fields: [
          { key: "api_token", label: "API Token", placeholder: "eyJhbGci••••••••", type: "password", hint: "Monday.com → Profile → Administration → API → Copy Personal Token" },
        ],
      },
      {
        type: "shortcut", label: "Shortcut",
        description: "Collect stories, epics, member access, and workflow states for change management evidence",
        fields: [
          { key: "api_token", label: "API Token", placeholder: "••••••••-••••-••••-••••-••••••••••••", type: "password", hint: "Shortcut → Profile → API Tokens → Generate Token" },
        ],
      },
    ],
  },
  {
    title: "Communication",
    integrations: [
      {
        type: "slack", label: "Slack", core: true,
        description: "Collect workspace users, admin users, and channel retention policies",
        fields: [
          { key: "bot_token", label: "Bot Token", placeholder: "xoxb-••••••••", type: "password", hint: "Starts with xoxb-" },
        ],
      },
      {
        type: "microsoft_teams", label: "Microsoft Teams",
        description: "Collect team members, admin roles, and messaging policies",
        fields: [
          { key: "tenant_id", label: "Tenant ID", placeholder: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" },
          { key: "client_id", label: "Client ID", placeholder: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" },
          { key: "client_secret", label: "Client Secret", placeholder: "••••••••••••", type: "password" },
        ],
      },
      {
        type: "zendesk", label: "Zendesk",
        description: "Collect support agents, SLA policies, and ticket workflow controls for availability and process evidence",
        fields: [
          { key: "subdomain", label: "Subdomain", placeholder: "mycompany", hint: "The part before .zendesk.com" },
          { key: "email", label: "Admin Email", placeholder: "admin@mycompany.com" },
          { key: "api_token", label: "API Token", placeholder: "••••••••••••", type: "password", hint: "Admin → Apps & Integrations → APIs → Zendesk API" },
        ],
      },
      {
        type: "zoom", label: "Zoom",
        description: "Collect meeting security settings, user roles, and recording retention policies for communication evidence",
        fields: [
          { key: "account_id", label: "Account ID", placeholder: "xxxxxxxxxxxxxxxxxxxxxxxx" },
          { key: "client_id", label: "Client ID", placeholder: "xxxxxxxxxxxxxxxxxxxxxxxx" },
          { key: "client_secret", label: "Client Secret", placeholder: "••••••••••••", type: "password", hint: "Zoom Marketplace → Build App → Server-to-Server OAuth" },
        ],
      },
      {
        type: "intercom", label: "Intercom",
        description: "Collect workspace members, data access controls, and security settings for customer data handling evidence",
        fields: [
          { key: "access_token", label: "Access Token", placeholder: "dG9r••••••••", type: "password", hint: "Intercom → Settings → Developers → Your Apps → Access Token" },
        ],
      },
    ],
  },
  {
    title: "Monitoring & Security",
    integrations: [
      {
        type: "cloudflare", label: "Cloudflare",
        description: "Collect WAF rules, access policies, DDoS protection settings, and audit logs for network security evidence",
        fields: [
          { key: "api_token", label: "API Token", placeholder: "••••••••••••", type: "password" },
          { key: "account_id", label: "Account ID", placeholder: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" },
        ],
      },
      {
        type: "crowdstrike", label: "CrowdStrike Falcon",
        description: "Collect endpoint detection coverage, policy status, and agent deployment for CC6.7 / CC6.8 evidence",
        fields: [
          { key: "client_id", label: "Client ID", placeholder: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" },
          { key: "client_secret", label: "Client Secret", placeholder: "••••••••••••", type: "password" },
          { key: "base_url", label: "Base URL", placeholder: "https://api.crowdstrike.com" },
        ],
      },
      {
        type: "jamf", label: "Jamf Pro", core: true,
        description: "Collect device enrollment, MDM profiles, disk encryption status, and patch compliance for Mac fleets",
        fields: [
          { key: "domain", label: "Jamf Domain", placeholder: "mycompany.jamfcloud.com" },
          { key: "username", label: "API Username", placeholder: "api-user" },
          { key: "password", label: "API Password", placeholder: "••••••••••••", type: "password" },
        ],
      },
      {
        type: "datadog", label: "Datadog", core: true,
        description: "Pull audit logs, alert rules, and monitoring coverage as evidence",
        fields: [
          { key: "api_key", label: "API Key", placeholder: "••••••••••••", type: "password" },
          { key: "app_key", label: "Application Key", placeholder: "••••••••••••", type: "password" },
          { key: "site", label: "Datadog Site", placeholder: "datadoghq.com" },
        ],
      },
      {
        type: "pagerduty", label: "PagerDuty",
        description: "Collect on-call schedules and incident response records",
        fields: [
          { key: "api_key", label: "API Key", placeholder: "••••••••••••", type: "password" },
        ],
      },
      {
        type: "sentry", label: "Sentry",
        description: "Collect error monitoring configuration and team access records",
        fields: [
          { key: "auth_token", label: "Auth Token", placeholder: "••••••••••••", type: "password" },
          { key: "org_slug", label: "Organization Slug", placeholder: "my-organization" },
        ],
      },
      {
        type: "stripe", label: "Stripe",
        description: "Collect payment security settings and access controls for PCI DSS evidence",
        fields: [
          { key: "api_key", label: "Restricted API Key", placeholder: "rk_live_••••••••", type: "password", hint: "Starts with rk_live_ (live) or rk_test_ (test)" },
        ],
      },
      {
        type: "snyk", label: "Snyk",
        description: "Pull dependency vulnerability findings and fix rates as continuous security evidence",
        fields: [
          { key: "api_token", label: "API Token", placeholder: "••••••••••••", type: "password" },
        ],
      },
      {
        type: "sentinelone", label: "SentinelOne",
        description: "Collect endpoint protection coverage, threat detection, and agent deployment status",
        fields: [
          { key: "management_url", label: "Management URL", placeholder: "https://mycompany.sentinelone.net" },
          { key: "api_token", label: "API Token", placeholder: "••••••••••••", type: "password" },
        ],
      },
      {
        type: "splunk", label: "Splunk",
        description: "Collect SIEM alerts, log retention policies, and security monitoring coverage",
        fields: [
          { key: "host", label: "Splunk Host", placeholder: "splunk.mycompany.com" },
          { key: "username", label: "Username", placeholder: "admin" },
          { key: "password", label: "Password", placeholder: "••••••••••••", type: "password" },
        ],
      },
      {
        type: "kolide", label: "Kolide",
        description: "Collect device health checks, compliance posture, and failed policy counts for CC6.8",
        fields: [
          { key: "api_key", label: "API Key", placeholder: "••••••••••••", type: "password" },
        ],
      },
      {
        type: "hackerone", label: "HackerOne",
        description: "Sync bug bounty program reports and remediation timelines as penetration testing evidence",
        fields: [
          { key: "api_username", label: "API Username", placeholder: "mycompany_api" },
          { key: "api_token", label: "API Token", placeholder: "••••••••••••", type: "password" },
        ],
      },
      {
        type: "new_relic", label: "New Relic",
        description: "Collect alert policies, user access, and observability coverage for availability evidence",
        fields: [
          { key: "api_key", label: "User API Key", placeholder: "NRAK-••••••••", type: "password", hint: "Starts with NRAK-" },
          { key: "account_id", label: "Account ID", placeholder: "1234567" },
        ],
      },
      {
        type: "tenable", label: "Tenable",
        description: "Pull vulnerability scan results and asset exposure for continuous CC7.1 evidence",
        fields: [
          { key: "access_key", label: "Access Key", placeholder: "••••••••••••", type: "password" },
          { key: "secret_key", label: "Secret Key", placeholder: "••••••••••••", type: "password" },
        ],
      },
      {
        type: "detectify", label: "Detectify",
        description: "Pull web application vulnerability findings, OWASP scan results, and remediation status for CC7.1 evidence",
        fields: [
          { key: "api_token", label: "API Token", placeholder: "••••••••••••••••••••••••••••••••", type: "password", hint: "Detectify → Team Settings → API Tokens → Create Token" },
        ],
      },
      {
        type: "nightfall", label: "Nightfall AI",
        description: "Collect DLP policy scan results, sensitive data findings, and violation counts for data classification evidence",
        fields: [
          { key: "api_key", label: "API Key", placeholder: "••••••••••••", type: "password", hint: "Nightfall Console → Settings → API Keys" },
        ],
      },
      {
        type: "opsgenie", label: "Opsgenie",
        description: "Collect on-call schedules, alert policies, and incident escalation chains for availability evidence",
        fields: [
          { key: "api_key", label: "API Key", placeholder: "••••••••-••••-••••-••••-••••••••••••", type: "password", hint: "Opsgenie → Settings → API key management" },
        ],
      },
    ],
  },
  {
    title: "HR & People",
    integrations: [
      {
        type: "bamboohr", label: "BambooHR", core: true,
        description: "Sync employee records, offboarding workflows, and org chart data",
        fields: [
          { key: "subdomain", label: "Subdomain", placeholder: "mycompany" },
          { key: "api_key", label: "API Key", placeholder: "••••••••••••", type: "password" },
        ],
      },
      {
        type: "kandji", label: "Kandji",
        description: "Collect Apple device enrollment, MDM compliance blueprints, and patch status for CC6.8",
        fields: [
          { key: "subdomain", label: "Subdomain", placeholder: "mycompany", hint: "The part before .kandji.io" },
          { key: "api_token", label: "API Token", placeholder: "••••••••••••", type: "password" },
        ],
      },
      {
        type: "vault", label: "HashiCorp Vault",
        description: "Collect secrets engine policies, auth methods, and audit log status for CC6.1 evidence",
        fields: [
          { key: "address", label: "Vault Address", placeholder: "https://vault.mycompany.com" },
          { key: "token", label: "Token", placeholder: "hvs.••••••••", type: "password", hint: "Needs read access to sys/auth, sys/policy, and sys/audit" },
        ],
      },
      {
        type: "kubernetes", label: "Kubernetes",
        description: "Collect namespaces, RBAC bindings, cluster roles, network policies, and pod inventory for infrastructure evidence",
        fields: [
          { key: "api_url", label: "API Server URL", placeholder: "https://k8s.mycompany.com:6443" },
          { key: "service_account_token", label: "Service Account Token", placeholder: "eyJhbGci...", type: "password", hint: "Bearer token from a read-only ServiceAccount" },
          { key: "verify_ssl", label: "Verify SSL", placeholder: "true", hint: "Set to false for self-signed certs" },
        ],
      },
      {
        type: "circleci", label: "CircleCI",
        description: "Collect pipeline runs, project settings, and organization access for change management and CI/CD evidence",
        fields: [
          { key: "api_token", label: "Personal API Token", placeholder: "••••••••••••", type: "password", hint: "CircleCI → User Settings → Personal API Tokens" },
          { key: "org_slug", label: "Org Slug (optional)", placeholder: "github/myorg", hint: "e.g. github/your-org-name" },
        ],
      },
      {
        type: "qualys", label: "Qualys",
        description: "Pull vulnerability scan results, asset inventory, and report history for continuous vulnerability management evidence",
        fields: [
          { key: "username", label: "Username", placeholder: "api-user" },
          { key: "password", label: "Password", placeholder: "••••••••••••", type: "password" },
          { key: "api_url", label: "API URL", placeholder: "https://qualysapi.qualys.com", hint: "Platform-specific — check your Qualys subscription portal" },
        ],
      },
      {
        type: "checkr", label: "Checkr",
        description: "Collect background check completion records for new hires as HR security evidence for CC1.4",
        fields: [
          { key: "api_key", label: "API Key", placeholder: "••••••••••••", type: "password", hint: "Checkr Dashboard → Account → Developer → API Keys" },
        ],
      },
      {
        type: "lattice", label: "Lattice",
        description: "Collect security training completion, performance reviews, and employee lifecycle records for people controls",
        fields: [
          { key: "api_token", label: "API Token", placeholder: "••••••••••••", type: "password", hint: "Lattice → Admin → Integrations → API Access" },
        ],
      },
      {
        type: "trainual", label: "Trainual",
        description: "Collect security policy acknowledgements, training completion rates, and onboarding records for CC1.2 evidence",
        fields: [
          { key: "api_key", label: "API Key", placeholder: "••••••••••••", type: "password", hint: "Trainual → Settings → Integrations → API Key" },
        ],
      },
      {
        type: "greenhouse", label: "Greenhouse",
        description: "Collect offer letters, onboarding steps, and new hire records for HR control evidence",
        fields: [
          { key: "api_key", label: "Harvest API Key", placeholder: "••••••••••••", type: "password", hint: "Greenhouse → Configure → Dev Center → API Credential Management" },
        ],
      },
    ],
  },
  {
    title: "CI/CD & DevOps",
    integrations: [
      {
        type: "jenkins", label: "Jenkins",
        description: "Collect build history, job configurations, and plugin inventory for CI/CD pipeline evidence",
        fields: [
          { key: "url", label: "Jenkins URL", placeholder: "https://jenkins.mycompany.com" },
          { key: "username", label: "Username", placeholder: "admin" },
          { key: "api_token", label: "API Token", placeholder: "••••••••••••", type: "password", hint: "Jenkins → Your username → Configure → API Token → Add new Token" },
        ],
      },
      {
        type: "azure_devops", label: "Azure DevOps",
        description: "Collect pipeline runs, branch policies, work items, and repository access for change management evidence",
        fields: [
          { key: "org", label: "Organization", placeholder: "mycompany", hint: "The org name in your Azure DevOps URL" },
          { key: "pat", label: "Personal Access Token", placeholder: "••••••••••••", type: "password", hint: "User Settings → Personal Access Tokens → New Token (Read scopes for Build, Code, Work Items)" },
        ],
      },
      {
        type: "argocd", label: "Argo CD",
        description: "Sync GitOps deployment history, RBAC policies, application health status, and sync records",
        fields: [
          { key: "server_url", label: "Server URL", placeholder: "https://argocd.mycompany.com" },
          { key: "token", label: "API Token", placeholder: "eyJhbGci••••••••", type: "password", hint: "Argo CD → Settings → Accounts → Generate Token (read-only account recommended)" },
        ],
      },
      {
        type: "elastic", label: "Elastic Security",
        description: "Collect SIEM detection rules, alert history, log retention policies, and security signal inventory",
        fields: [
          { key: "cloud_id", label: "Cloud ID", placeholder: "my-deployment:••••••••", hint: "Found in Elastic Cloud → Deployment → Overview" },
          { key: "api_key", label: "API Key", placeholder: "••••••••••••:••••••••••••", type: "password", hint: "Kibana → Stack Management → API Keys → Create API Key (read permissions)" },
        ],
      },
    ],
  },
  {
    title: "Coming Soon",
    integrations: [
      { type: "workday",      label: "Workday",        comingSoon: true, description: "Sync employee records, org chart, and lifecycle events for HR compliance evidence", fields: [] },
      { type: "gusto",        label: "Gusto",          comingSoon: true, description: "Collect payroll runs, employee onboarding, and benefits enrollment records", fields: [] },
      { type: "dynatrace",    label: "Dynatrace",      comingSoon: true, description: "Pull availability monitoring, SLO compliance, and alert configurations", fields: [] },
      { type: "sumo_logic",   label: "Sumo Logic",     comingSoon: true, description: "Collect log retention settings, access controls, and audit events", fields: [] },
      { type: "lacework",     label: "Lacework",       comingSoon: true, description: "Pull cloud security posture findings, anomaly detections, and compliance benchmarks", fields: [] },
      { type: "carbon_black", label: "Carbon Black",   comingSoon: true, description: "Collect endpoint sensor deployment, policy enforcement, and threat detections", fields: [] },
      { type: "rapid7",       label: "Rapid7",         comingSoon: true, description: "Pull vulnerability scan results, asset risk scores, and remediation tracking", fields: [] },
      { type: "prisma_cloud", label: "Prisma Cloud",   comingSoon: true, description: "Collect CSPM findings, compliance benchmarks, and misconfiguration alerts", fields: [] },
      { type: "freshdesk",    label: "Freshdesk",      comingSoon: true, description: "Collect support agents, SLA configurations, and ticket workflow policies", fields: [] },
      { type: "secureframe",  label: "Secureframe",    comingSoon: true, description: "Import existing compliance posture and evidence library for cross-platform migration", fields: [] },
      { type: "drata",        label: "Drata",          comingSoon: true, description: "Import existing controls and evidence library for cross-platform migration", fields: [] },
    ],
  },
];

const ALL_DEFS: IntegrationDef[] = INTEGRATION_GROUPS.flatMap((g) => g.integrations);

// All integrations collect real evidence — no stubs
const STUB_TYPES = new Set<string>();

// ── Setup guides ──────────────────────────────────────────────────────────────
type SetupGuide = { steps: string[]; url?: string };

const SETUP_GUIDES: Record<string, SetupGuide> = {
  aws: {
    url: "https://console.aws.amazon.com/iam/home#/users/create",
    steps: [
      "Go to IAM Console → Users → Create user",
      "Attach policy: ReadOnlyAccess (or a custom read-only policy)",
      "Security credentials tab → Create access key → Application outside AWS",
      "Copy the Access Key ID and Secret Access Key",
    ],
  },
  github: {
    url: "https://github.com/settings/tokens/new",
    steps: [
      "GitHub → Settings → Developer Settings → Personal access tokens",
      "Tokens (classic) → Generate new token",
      "Select scopes: repo, read:org (org scope needed for organization accounts)",
      "Copy the generated token (starts with ghp_)",
      "In the field below, enter your GitHub org name OR your personal username — both work",
    ],
  },
  slack: {
    url: "https://api.slack.com/apps",
    steps: [
      "Go to api.slack.com/apps → Create New App → From scratch",
      "OAuth & Permissions → Add Bot Token Scopes: channels:read, users:read, team:read",
      "Install to Workspace → copy the Bot User OAuth Token",
    ],
  },
  google_workspace: {
    url: "https://console.cloud.google.com/iam-admin/serviceaccounts",
    steps: [
      "Google Cloud Console → Enable the Admin SDK API",
      "IAM & Admin → Service Accounts → Create service account",
      "Create a JSON key and download it",
      "In Google Workspace Admin → Security → API controls → Domain-wide delegation → add the service account's client ID",
    ],
  },
  okta: {
    steps: [
      "Log in to your Okta Admin Console",
      "Security → API → Tokens → Create Token",
      "Copy the token value — it is shown only once",
      "Your domain is the subdomain in your Okta URL (e.g. mycompany.okta.com)",
    ],
  },
  azure_ad: {
    url: "https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade",
    steps: [
      "Azure Portal → Azure Active Directory → App registrations → New registration",
      "Certificates & secrets → New client secret → copy the value",
      "API permissions → Add: User.Read.All, Group.Read.All (Microsoft Graph) → Grant admin consent",
      "Copy Tenant ID and Client ID from the app overview page",
    ],
  },
  jira: {
    url: "https://id.atlassian.com/manage-profile/security/api-tokens",
    steps: [
      "Go to id.atlassian.com → Account Settings → Security",
      "Create and manage API tokens → Create API token",
      "Use your Atlassian account email as the admin email",
      "Your domain is yourcompany.atlassian.net",
    ],
  },
  gitlab: {
    url: "https://gitlab.com/-/user_settings/personal_access_tokens",
    steps: [
      "GitLab → User Settings (top right) → Access Tokens",
      "Add new token → select scopes: api, read_user",
      "Copy the token (starts with glpat-)",
    ],
  },
  linear: {
    url: "https://linear.app/settings/api",
    steps: [
      "Linear → Settings → API",
      "Create new API key",
      "Copy the key (starts with lin_api_)",
    ],
  },
  notion: {
    url: "https://www.notion.so/my-integrations",
    steps: [
      "notion.so/my-integrations → New integration",
      "Set capabilities: Read content, Read user information",
      "Copy the Internal Integration Token (starts with secret_)",
    ],
  },
  cloudflare: {
    url: "https://dash.cloudflare.com/profile/api-tokens",
    steps: [
      "Cloudflare dashboard → My Profile → API Tokens",
      "Create Token → Custom token",
      "Add permissions: Zone Settings:Read, Zone:Read, Audit Logs:Read",
      "Copy the token and find your Account ID on the main dashboard sidebar",
    ],
  },
  datadog: {
    url: "https://app.datadoghq.com/organization-settings/api-keys",
    steps: [
      "Datadog → Organization Settings → API Keys → New Key",
      "Organization Settings → Application Keys → New Key",
      "Copy both the API Key and Application Key",
      "Your site is datadoghq.com (EU: datadoghq.eu)",
    ],
  },
  pagerduty: {
    url: "https://app.pagerduty.com/api_keys",
    steps: [
      "PagerDuty → Integrations → Developer Tools → API Access Keys",
      "Create New API Key",
      "Copy the key (shown once)",
    ],
  },
  sentry: {
    url: "https://sentry.io/settings/account/api/auth-tokens/new-token/",
    steps: [
      "Sentry → Settings → Account → API → Auth Tokens",
      "Create New Token",
      "Select scopes: org:read, project:read, team:read",
      "Copy the token and find your org slug in Settings → Organization",
    ],
  },
  stripe: {
    url: "https://dashboard.stripe.com/apikeys",
    steps: [
      "Stripe Dashboard → Developers → API keys",
      "Create restricted key",
      "Enable read permissions for: Accounts, Balance, Customers",
      "Copy the key (starts with rk_live_ or rk_test_)",
    ],
  },
  terraform_cloud: {
    url: "https://app.terraform.io/app/settings/tokens",
    steps: [
      "Terraform Cloud → User Settings (top right) → Tokens",
      "Create an API token",
      "Copy the token and note your organization name",
    ],
  },
  "1password": {
    url: "https://my.1password.com/integrations/infrastructure/",
    steps: [
      "1Password.com → Developer → Service Accounts",
      "Create a new service account and grant access to relevant vaults",
      "Copy the service account token (starts with ops_)",
    ],
  },
  rippling: {
    steps: [
      "Log in to Rippling as an admin",
      "Go to IT → API → API Keys",
      "Create a new API key and copy it",
    ],
  },
  bamboohr: {
    steps: [
      "Log in to BambooHR",
      "Click your profile picture (top right) → API Keys",
      "Add New Key → copy the key",
      "Your subdomain is the part before .bamboohr.com in your URL",
    ],
  },
  google_cloud: {
    url: "https://console.cloud.google.com/iam-admin/serviceaccounts",
    steps: [
      "Google Cloud Console → IAM & Admin → Service Accounts → Create service account",
      "Grant roles: Viewer, Security Reviewer",
      "Create JSON key → download it",
      "Paste the full JSON content and enter your project ID",
    ],
  },
  microsoft_teams: {
    url: "https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade",
    steps: [
      "Azure Portal → Azure Active Directory → App registrations → New registration",
      "Certificates & secrets → New client secret → copy the value",
      "API permissions → Add: Team.ReadBasic.All, TeamMember.Read.All (Microsoft Graph)",
      "Copy Tenant ID, Client ID, and the client secret",
    ],
  },
  crowdstrike: {
    url: "https://falcon.crowdstrike.com/support/api-clients-and-keys",
    steps: [
      "CrowdStrike Falcon → Support → API Clients and Keys",
      "Add new API client",
      "Enable Read scopes: Hosts, Detections, Prevention Policy",
      "Copy Client ID and Client Secret (shown once on creation)",
    ],
  },
  jamf: {
    steps: [
      "Log in to Jamf Pro as admin",
      "Settings → System → User Accounts & Groups → New",
      "Create a user with Read-Only Standard account privileges",
      "Enter your Jamf Pro server URL (e.g. https://mycompany.jamfcloud.com)",
    ],
  },
  vercel: {
    url: "https://vercel.com/account/tokens",
    steps: [
      "Vercel → Settings (top right) → Tokens",
      "Create Token → choose a name and expiry",
      "Copy the token",
      "Team ID is optional — find it in your team Settings → General",
    ],
  },
  duo: {
    steps: [
      "Log in to Duo Admin Panel → Applications → Protect an Application",
      "Search for 'Admin API' and click Protect",
      "Copy the Integration Key, Secret Key, and API Hostname",
      "Grant the application 'Read resource' permission",
    ],
  },
  wiz: {
    steps: [
      "Wiz portal → Settings → Service Accounts → Add Service Account",
      "Select role: Security Auditor (read-only)",
      "Copy Client ID and Client Secret (shown once)",
      "Your API endpoint is shown in Settings → General (e.g. https://api.us1.app.wiz.io/graphql)",
    ],
  },
  snyk: {
    url: "https://app.snyk.io/account",
    steps: [
      "Snyk → Account Settings → Auth Token",
      "Click 'click to show' to reveal your API token",
      "Copy the token",
    ],
  },
  sentinelone: {
    steps: [
      "SentinelOne console → Settings → Users → Service Users",
      "Create new service user with Viewer role",
      "Generate API token and copy it",
      "Your management URL is your SentinelOne console URL (e.g. https://mycompany.sentinelone.net)",
    ],
  },
  splunk: {
    steps: [
      "Log in to Splunk Web as admin",
      "Use your Splunk server hostname or IP as the host",
      "Provide admin credentials (read-only user recommended)",
      "Ensure the REST API port (8089) is accessible",
    ],
  },
  kolide: {
    url: "https://k2.kolide.com/settings/api",
    steps: [
      "Kolide → Settings → API Keys",
      "Create a new API key with Read access",
      "Copy the key",
    ],
  },
  hackerone: {
    url: "https://hackerone.com/settings/api_token",
    steps: [
      "HackerOne → Settings → API Token",
      "Create a new API token",
      "Copy the API Username and Token (both are needed)",
    ],
  },
  confluence: {
    url: "https://id.atlassian.com/manage-profile/security/api-tokens",
    steps: [
      "Go to id.atlassian.com → Account Settings → Security → API Tokens",
      "Create an API token and copy it",
      "Use your Atlassian email as the admin email",
      "Your domain is yourcompany.atlassian.net",
    ],
  },
  servicenow: {
    steps: [
      "Log in to your ServiceNow instance as admin",
      "Create a dedicated read-only user for API access",
      "Grant the user the 'rest_api_explorer' and 'snc_read_only' roles",
      "Your instance name is the part before .service-now.com",
    ],
  },
  kandji: {
    steps: [
      "Kandji → Settings → Access → API Token",
      "Create a new API token with Read access",
      "Copy the token",
      "Your subdomain is the part before .kandji.io in your console URL",
    ],
  },
  new_relic: {
    url: "https://one.newrelic.com/api-keys",
    steps: [
      "New Relic → API Keys (top right menu)",
      "Create key → User key → name it 'TraceLayer'",
      "Copy the key (starts with NRAK-)",
      "Find your Account ID in the URL or under Account Settings",
    ],
  },
  tenable: {
    url: "https://app.tenable.io/#/api-keys",
    steps: [
      "Tenable.io → Settings → My Account → API Keys",
      "Generate new API keys",
      "Copy both the Access Key and Secret Key (shown once)",
    ],
  },
  vault: {
    steps: [
      "Create a read-only Vault policy: path \"sys/*\" { capabilities = [\"read\", \"list\"] }",
      "Assign the policy to a token: vault token create -policy=tracelayer-reader",
      "Copy the token (starts with hvs.)",
      "Your Vault address is the URL you use to access Vault (e.g. https://vault.mycompany.com)",
    ],
  },
  jumpcloud: {
    url: "https://console.jumpcloud.com/#/settings",
    steps: [
      "Log in to JumpCloud Admin Console",
      "Click your avatar (top right) → API Settings",
      "Copy the API Key shown — it grants read access to your directory",
    ],
  },
  bitbucket: {
    url: "https://bitbucket.org/account/settings/app-passwords/new",
    steps: [
      "Bitbucket → Personal Settings → App passwords → Create app password",
      "Grant permissions: Account: Read, Workspace membership: Read, Repositories: Read",
      "Copy the generated password (shown once)",
      "Your workspace slug is the short name in your Bitbucket URLs (e.g. bitbucket.org/{workspace}/...)",
    ],
  },
  zendesk: {
    url: "https://support.zendesk.com/hc/en-us/articles/4408889192858",
    steps: [
      "Zendesk Admin → Apps & Integrations → APIs → Zendesk API",
      "Enable Token Access if not already on",
      "Click 'Add API token', give it a name, copy the token",
      "Your subdomain is the part before .zendesk.com in your URL",
    ],
  },
  kubernetes: {
    steps: [
      "Create a read-only ClusterRole and ServiceAccount in your cluster",
      "kubectl create serviceaccount tracelayer-reader -n kube-system",
      "kubectl create clusterrolebinding tracelayer-reader --clusterrole=view --serviceaccount=kube-system:tracelayer-reader",
      "kubectl create token tracelayer-reader -n kube-system --duration=8760h",
      "Your API URL is the server address from kubectl cluster-info",
    ],
  },
  circleci: {
    url: "https://app.circleci.com/settings/user/tokens",
    steps: [
      "CircleCI → User Settings → Personal API Tokens → Create New Token",
      "Give it a name (e.g. TraceLayer) and copy the token",
      "Org slug format: github/your-org-name or bitbucket/your-org-name (optional)",
    ],
  },
  qualys: {
    steps: [
      "Log in to your Qualys subscription portal",
      "Go to Users → Add User — create an API-only user with Reader role",
      "Your API URL is platform-specific: US1 = qualysapi.qualys.com, EU1 = qualysapi.eu.qualys.com",
      "Check help.qualys.com → Get Started → Qualys Platform URLs for your region",
    ],
  },
};

// ── Upgrade Modal ─────────────────────────────────────────────────────────────
function UpgradeModal({ onClose }: { onClose: () => void }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const handleUpgrade = async () => {
    setLoading(true);
    try {
      const { checkout_url } = await api.createCheckout();
      await openPaddleCheckout(checkout_url);
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
  const [guideOpen, setGuideOpen] = useState(true);

  const guide = SETUP_GUIDES[def.type];

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
        <div className="flex items-center gap-3 mb-4">
          <LogoBadge type={def.type} size={44}/>
          <div>
            <h2 className="text-base font-semibold text-gray-900">Connect {def.label}</h2>
            <p className="text-sm text-gray-500">{def.description}</p>
          </div>
        </div>

        {/* Setup guide */}
        {guide && (
          <div className="mb-4 border border-blue-100 rounded-xl overflow-hidden">
            <button
              type="button"
              onClick={() => setGuideOpen((v) => !v)}
              className="w-full flex items-center justify-between px-3.5 py-2.5 bg-blue-50 hover:bg-blue-100 transition-colors text-left"
            >
              <span className="flex items-center gap-2 text-xs font-semibold text-blue-700">
                <BookOpen className="w-3.5 h-3.5 shrink-0"/>
                How to find your credentials
              </span>
              <span className="text-blue-400 text-[10px] font-medium">{guideOpen ? "Hide ▲" : "Show ▼"}</span>
            </button>
            {guideOpen && (
              <div className="px-3.5 py-3 bg-blue-50/50 space-y-2.5">
                <ol className="space-y-1.5">
                  {guide.steps.map((step, i) => (
                    <li key={i} className="flex gap-2.5 text-xs text-gray-700 leading-relaxed">
                      <span className="shrink-0 w-4 h-4 rounded-full bg-blue-200 text-blue-700 flex items-center justify-center text-[9px] font-bold mt-0.5">
                        {i + 1}
                      </span>
                      <span>{step}</span>
                    </li>
                  ))}
                </ol>
                {guide.url && (
                  <a
                    href={guide.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:text-blue-700 mt-1"
                  >
                    Open {def.label} settings
                    <ExternalLink className="w-3 h-3"/>
                  </a>
                )}
              </div>
            )}
          </div>
        )}

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
              {f.hint && <p className="mt-1 text-[11px] text-gray-400">{f.hint}</p>}
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
          {def.core && !connected && !def.comingSoon && (
            <span title="Actively maintained by TraceLayer" className="text-[10px] font-bold uppercase tracking-wide text-brand-600 bg-brand-50 px-1.5 py-0.5 rounded-md">Core</span>
          )}
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
    const before = integrations.find((i) => i.integration_type === type)?.last_collected_at;
    try {
      await api.triggerCollect(type);
      // Poll every 3s for up to 30s waiting for last_collected_at to update
      await new Promise<void>((resolve) => {
        let polls = 0;
        const timer = setInterval(async () => {
          polls++;
          try {
            const updated = await api.getIntegrations();
            const current = updated.find((i) => i.integration_type === type);
            if (current?.last_collected_at !== before || polls >= 10) {
              clearInterval(timer);
              setIntegrations(updated);
              showToast(polls >= 10 ? `Sync running in background` : `${type} synced successfully`);
              resolve();
            }
          } catch {
            clearInterval(timer);
            resolve();
          }
        }, 3000);
      });
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Failed to start sync");
    } finally {
      setCollecting(null);
    }
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

      {/* Compliance checklist — collapsed by default, at the bottom */}
      <div className="mt-10">
        <ComplianceChecklist connectedTypes={integrations.map((i) => i.integration_type)} />
      </div>
    </div>
  );
}

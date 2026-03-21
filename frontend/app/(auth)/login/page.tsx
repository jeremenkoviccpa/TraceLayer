"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { useAuth } from "@/components/auth-provider";
import { api } from "@/lib/api";
import { Eye, EyeOff, AlertCircle, CheckCircle2, ShieldCheck, Building2 } from "lucide-react";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  // SSO state
  const [ssoCompanyId, setSsoCompanyId] = useState<string | null>(null);
  const [ssoChecking, setSsoChecking] = useState(false);
  // 2FA state
  const [totpStep, setTotpStep] = useState(false);
  const [totpToken, setTotpToken] = useState("");
  const [totpCode, setTotpCode] = useState("");

  const handleEmailBlur = async () => {
    const domain = email.split("@")[1];
    if (!domain) return;
    setSsoChecking(true);
    try {
      const result = await api.checkSSODomain(domain);
      setSsoCompanyId(result.sso_enabled && result.company_id ? result.company_id : null);
    } catch {
      setSsoCompanyId(null);
    } finally {
      setSsoChecking(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await login(email, password);
      if (result?.requires_2fa && result.totp_token) {
        setTotpToken(result.totp_token);
        setTotpStep(true);
        setLoading(false);
        return;
      }
      const company = await api.getCompany();
      router.push(company.is_partner_account ? "/partner/clients" : "/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleTotpSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.verify2FA(totpToken, totpCode);
      const company = await api.getCompany();
      router.push(company.is_partner_account ? "/partner/clients" : "/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Invalid code");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left branded panel */}
      <div className="hidden lg:flex lg:w-[45%] bg-gradient-to-br from-brand-500 via-brand-600 to-brand-900 flex-col justify-between p-12 relative overflow-hidden">
        {/* Background decoration */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 right-0 w-96 h-96 bg-white rounded-full -translate-y-1/2 translate-x-1/2" />
          <div className="absolute bottom-0 left-0 w-64 h-64 bg-white rounded-full translate-y-1/2 -translate-x-1/2" />
        </div>

        <Link href="/" aria-label="Go to TraceLayer landing page" className="relative flex items-center gap-3">
          <div className="w-10 h-10 bg-white/15 rounded-xl flex items-center justify-center backdrop-blur-sm border border-white/20 overflow-hidden">
            <Image src="/logo-icon.png" alt="TraceLayer" width={32} height={32} />
          </div>
          <span className="text-xl font-bold text-white tracking-tight">TraceLayer</span>
        </Link>

        <div className="relative">
          <h2 className="text-3xl font-bold text-white leading-tight mb-4">
            Continuous compliance.<br />Zero manual effort.
          </h2>
          <p className="text-white/65 text-base mb-10 leading-relaxed">
            Collect evidence automatically across your cloud stack and stay audit-ready 24/7.
          </p>
          <div className="space-y-3">
            {[
              "SOC 2 free · ISO 27001, HIPAA & more on Growth",
              "Automatic evidence collection from AWS, GitHub & more",
              "AI-powered compliance advisor",
            ].map((f) => (
              <div key={f} className="flex items-center gap-3">
                <div className="w-5 h-5 rounded-full bg-white/15 flex items-center justify-center shrink-0 border border-white/20">
                  <CheckCircle2 className="w-3 h-3 text-white" />
                </div>
                <span className="text-white/75 text-sm">{f}</span>
              </div>
            ))}
          </div>
        </div>

        <p className="relative text-white/35 text-xs">© 2025 TraceLayer. All rights reserved.</p>
      </div>

      {/* Right form panel */}
      <div className="flex-1 flex items-center justify-center p-6 bg-white">
        <div className="w-full max-w-sm animate-fade-in">
          {/* Mobile logo */}
          <Link href="/" aria-label="Go to TraceLayer landing page" className="flex items-center gap-2.5 mb-10 lg:hidden">
            <Image src="/logo-icon.png" alt="TraceLayer" width={36} height={36} className="rounded-xl" />
            <span className="text-lg font-bold text-gray-900">TraceLayer</span>
          </Link>

          <div className="mb-8">
            <h1 className="text-2xl font-bold text-gray-900 mb-1">Welcome back</h1>
            <p className="text-gray-500 text-sm">Sign in to your account to continue</p>
          </div>

          {/* Google OAuth */}
          <a
            href={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/v1/auth/google`}
            className="w-full flex items-center justify-center gap-3 border border-gray-200 rounded-xl py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Continue with Google
          </a>

          <div className="relative my-1">
            <div className="absolute inset-0 flex items-center"><span className="w-full border-t border-gray-100" /></div>
            <div className="relative flex justify-center"><span className="bg-white px-3 text-xs text-gray-400">or</span></div>
          </div>

          {totpStep ? (
            <form onSubmit={handleTotpSubmit} className="space-y-4">
              <div className="flex items-center gap-3 bg-brand-50 border border-brand-100 rounded-xl px-4 py-3 mb-2">
                <ShieldCheck className="w-5 h-5 text-brand-600 shrink-0" />
                <div>
                  <p className="text-sm font-semibold text-brand-900">Two-factor authentication</p>
                  <p className="text-xs text-brand-600">Enter the 6-digit code from your authenticator app</p>
                </div>
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm flex items-center gap-2 animate-slide-up">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  {error}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Authentication code</label>
                <input
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9A-Fa-f]*"
                  value={totpCode}
                  onChange={(e) => setTotpCode(e.target.value.replace(/\s/g, ""))}
                  required
                  autoFocus
                  maxLength={8}
                  className="input text-center tracking-[0.3em] text-lg font-mono"
                  placeholder="000000"
                />
                <p className="text-xs text-gray-400 mt-1.5">You can also enter a backup code</p>
              </div>

              <button
                type="submit"
                disabled={loading || totpCode.length < 6}
                className="btn-primary w-full mt-2 py-2.5 justify-center"
              >
                {loading ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Verifying…
                  </>
                ) : "Verify"}
              </button>

              <button
                type="button"
                onClick={() => { setTotpStep(false); setError(""); setTotpCode(""); }}
                className="w-full text-center text-sm text-gray-500 hover:text-gray-700"
              >
                ← Back to login
              </button>
            </form>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm flex items-center gap-2 animate-slide-up">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  {error}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => { setEmail(e.target.value); setSsoCompanyId(null); }}
                  onBlur={handleEmailBlur}
                  required
                  autoFocus
                  className="input"
                  placeholder="you@company.com"
                />
              </div>

              {ssoCompanyId && (
                <a
                  href={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/v1/auth/sso/${ssoCompanyId}/login`}
                  className="w-full flex items-center justify-center gap-3 border border-brand-200 bg-brand-50 rounded-xl py-2.5 text-sm font-medium text-brand-700 hover:bg-brand-100 transition-colors"
                >
                  <Building2 className="w-4 h-4" />
                  Continue with SSO
                </a>
              )}

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-sm font-medium text-gray-700">Password</label>
                  <Link href="/forgot-password" className="text-xs text-brand-600 hover:text-brand-700 font-medium">
                    Forgot password?
                  </Link>
                </div>
                <div className="relative">
                  <input
                    type={showPw ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="input pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPw(!showPw)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                    tabIndex={-1}
                  >
                    {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-primary w-full mt-2 py-2.5 justify-center"
              >
                {loading ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Signing in…
                  </>
                ) : "Sign in"}
              </button>
            </form>
          )}

          <p className="text-center text-sm text-gray-500 mt-8">
            Don&apos;t have an account?{" "}
            <Link href="/register" className="text-brand-600 hover:text-brand-700 font-semibold">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

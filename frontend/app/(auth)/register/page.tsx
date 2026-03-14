"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { useAuth } from "@/components/auth-provider";
import { Eye, EyeOff, AlertCircle, CheckCircle2 } from "lucide-react";

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [companyName, setCompanyName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(email, password, companyName);
      router.push("/onboarding");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left branded panel */}
      <div className="hidden lg:flex lg:w-[45%] bg-gradient-to-br from-brand-500 via-brand-600 to-brand-900 flex-col justify-between p-12 relative overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 right-0 w-96 h-96 bg-white rounded-full -translate-y-1/2 translate-x-1/2" />
          <div className="absolute bottom-0 left-0 w-64 h-64 bg-white rounded-full translate-y-1/2 -translate-x-1/2" />
        </div>

        <div className="relative flex items-center gap-3">
          <div className="w-10 h-10 bg-white/15 rounded-xl flex items-center justify-center backdrop-blur-sm border border-white/20 overflow-hidden">
            <Image src="/logo-icon.png" alt="TraceLayer" width={32} height={32} />
          </div>
          <span className="text-xl font-bold text-white tracking-tight">TraceLayer</span>
        </div>

        <div className="relative">
          <h2 className="text-3xl font-bold text-white leading-tight mb-4">
            Audit-ready in<br />minutes, not months.
          </h2>
          <p className="text-white/65 text-base mb-10 leading-relaxed">
            Connect your tools and TraceLayer starts collecting compliance evidence automatically.
          </p>
          <div className="space-y-3">
            {[
              "Free plan — no credit card required",
              "Connect AWS, GitHub, Slack and more",
              "Real-time compliance scoring",
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
          <div className="flex items-center gap-2.5 mb-10 lg:hidden">
            <Image src="/logo-icon.png" alt="TraceLayer" width={36} height={36} className="rounded-xl" />
            <span className="text-lg font-bold text-gray-900">TraceLayer</span>
          </div>

          <div className="mb-8">
            <h1 className="text-2xl font-bold text-gray-900 mb-1">Create your account</h1>
            <p className="text-gray-500 text-sm">Get started — it&apos;s free</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm flex items-center gap-2 animate-slide-up">
                <AlertCircle className="w-4 h-4 shrink-0" />
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Company name</label>
              <input
                type="text"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                required
                autoFocus
                className="input"
                placeholder="Acme Inc."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Work email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="input"
                placeholder="you@company.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Password</label>
              <div className="relative">
                <input
                  type={showPw ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={8}
                  className="input pr-10"
                  placeholder="Min. 8 characters"
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
                  Creating account…
                </>
              ) : "Create account"}
            </button>
          </form>

          <p className="text-center text-xs text-gray-400 mt-4">
            By creating an account you agree to our{" "}
            <Link href="/terms" className="underline hover:text-gray-600">Terms</Link>
            {" "}and{" "}
            <Link href="/privacy" className="underline hover:text-gray-600">Privacy Policy</Link>.
          </p>

          <p className="text-center text-sm text-gray-500 mt-6">
            Already have an account?{" "}
            <Link href="/login" className="text-brand-600 hover:text-brand-700 font-semibold">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

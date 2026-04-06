"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { api } from "@/lib/api";
import { Eye, EyeOff, AlertCircle, Shield, CheckCircle2 } from "lucide-react";

export default function RegisterAgencyPage() {
  const router = useRouter();
  const [agencyName, setAgencyName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.registerAgency(email, password, agencyName);
      router.push("/agency/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left panel */}
      <div className="hidden lg:flex lg:w-[45%] bg-gradient-to-br from-slate-800 via-slate-900 to-slate-950 flex-col justify-between p-12 relative overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 right-0 w-96 h-96 bg-brand-400 rounded-full -translate-y-1/2 translate-x-1/2" />
          <div className="absolute bottom-0 left-0 w-64 h-64 bg-brand-400 rounded-full translate-y-1/2 -translate-x-1/2" />
        </div>

        <Link href="/" className="relative flex items-center gap-3">
          <div className="w-10 h-10 bg-white/15 rounded-xl flex items-center justify-center backdrop-blur-sm border border-white/20 overflow-hidden">
            <Image src="/logo-icon.png" alt="TraceLayer" width={32} height={32} />
          </div>
          <span className="text-xl font-bold text-white tracking-tight">TraceLayer</span>
        </Link>

        <div className="relative">
          <div className="flex items-center gap-2 mb-4">
            <Shield className="w-5 h-5 text-brand-400" />
            <span className="text-sm font-semibold text-brand-400 uppercase tracking-wider">Agency Portal</span>
          </div>
          <h2 className="text-3xl font-bold text-white leading-tight mb-4">
            List your agency and manage pen tests in one place.
          </h2>
          <p className="text-white/60 text-base mb-10 leading-relaxed">
            Register once. Customers find you through the directory and assign pen tests directly to your agency portal.
          </p>
          <div className="space-y-3">
            {[
              "Get discovered by compliance teams",
              "Receive test assignments directly",
              "Fill in findings and reports in-portal",
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

        <p className="relative text-white/30 text-xs">© 2026 TraceLayer. All rights reserved.</p>
      </div>

      {/* Right form */}
      <div className="flex-1 flex items-center justify-center p-6 bg-white">
        <div className="w-full max-w-sm">
          <Link href="/" className="flex items-center gap-2.5 mb-10 lg:hidden">
            <Image src="/logo-icon.png" alt="TraceLayer" width={36} height={36} className="rounded-xl" />
            <span className="text-lg font-bold text-gray-900">TraceLayer</span>
          </Link>

          <div className="mb-6">
            <h1 className="text-2xl font-bold text-gray-900 mb-1">Register your agency</h1>
            <p className="text-gray-500 text-sm">Join the TraceLayer pen test directory</p>
          </div>

          <div className="mb-5 bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-xs text-slate-600 leading-relaxed">
            As an agency you receive pen test assignments from customers and fill in all results directly in the portal.
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Agency / firm name</label>
              <input
                type="text"
                value={agencyName}
                onChange={(e) => setAgencyName(e.target.value)}
                required
                autoFocus
                className="input"
                placeholder="Acme Security Labs"
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
                placeholder="you@agencydomain.com"
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
              ) : "Create Agency Account"}
            </button>
          </form>

          <p className="text-center text-xs text-gray-400 mt-4">
            By creating an account you agree to our{" "}
            <Link href="/terms" className="underline hover:text-gray-600">Terms</Link>
            {" "}and{" "}
            <Link href="/privacy" className="underline hover:text-gray-600">Privacy Policy</Link>.
          </p>

          <p className="text-center text-sm text-gray-500 mt-4">
            Already have an account?{" "}
            <Link href="/login" className="text-brand-600 hover:text-brand-700 font-semibold">Sign in</Link>
          </p>

          <p className="text-center text-xs text-gray-400 mt-2">
            Not an agency?{" "}
            <Link href="/register" className="underline hover:text-gray-600">Register a company</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

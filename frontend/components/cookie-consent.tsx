"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

const COOKIE_KEY = "tl_cookie_consent";

export function CookieConsent() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem(COOKIE_KEY)) {
      // Small delay so it doesn't flash on first paint
      const t = setTimeout(() => setVisible(true), 800);
      return () => clearTimeout(t);
    }
  }, []);

  const accept = () => {
    localStorage.setItem(COOKIE_KEY, "accepted");
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div className="fixed bottom-4 left-4 right-4 z-50 flex justify-center pointer-events-none">
      <div className="pointer-events-auto w-full max-w-xl bg-white border border-gray-200 rounded-2xl shadow-xl px-5 py-4 flex flex-col sm:flex-row sm:items-center gap-3">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <span className="text-lg shrink-0 mt-0.5">🍪</span>
          <p className="text-sm text-gray-600 leading-snug">
            We use essential cookies to keep you signed in and save your preferences — nothing else.{" "}
            <Link href="/privacy" className="text-gray-900 underline underline-offset-2 hover:text-brand-600 transition-colors font-medium">
              Privacy Policy
            </Link>
          </p>
        </div>
        <button
          onClick={accept}
          className="shrink-0 bg-gray-900 text-white text-sm font-semibold px-4 py-2 rounded-xl hover:bg-gray-800 transition-colors whitespace-nowrap"
        >
          Got it
        </button>
      </div>
    </div>
  );
}

"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

const COOKIE_KEY = "tl_cookie_consent";

export function CookieConsent() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem(COOKIE_KEY)) setVisible(true);
  }, []);

  const accept = () => {
    localStorage.setItem(COOKIE_KEY, "accepted");
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 p-4 md:p-6">
      <div className="max-w-2xl mx-auto bg-gray-900 text-white rounded-xl shadow-2xl px-5 py-4 flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <p className="text-sm text-gray-300 flex-1">
          We use essential cookies to keep you signed in and remember your preferences.{" "}
          <Link href="/privacy" className="underline text-gray-200 hover:text-white">
            Privacy Policy
          </Link>
        </p>
        <div className="flex gap-2 shrink-0">
          <button
            onClick={accept}
            className="bg-white text-gray-900 text-sm font-semibold px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            Accept
          </button>
        </div>
      </div>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, XCircle, Info, X } from "lucide-react";

type ToastItem = { id: number; msg: string; type: "success" | "error" | "info" };

const ICONS = {
  success: <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />,
  error:   <XCircle     className="w-4 h-4 text-red-500 shrink-0" />,
  info:    <Info        className="w-4 h-4 text-blue-500 shrink-0" />,
};

const STYLES = {
  success: "border-emerald-100",
  error:   "border-red-100",
  info:    "border-blue-100",
};

let _id = 0;

/** Fire-and-forget toast from anywhere — dispatches a custom DOM event. */
export function showToast(msg: string, type: "success" | "error" | "info" = "success") {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("app-toast", { detail: { msg, type } }));
  }
}

export default function Toaster() {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  useEffect(() => {
    const handler = (e: Event) => {
      const { msg, type } = (e as CustomEvent).detail;
      const id = ++_id;
      setToasts((prev) => [...prev, { id, msg, type }]);
      setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
    };
    window.addEventListener("app-toast", handler);
    return () => window.removeEventListener("app-toast", handler);
  }, []);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-5 right-5 z-[9999] flex flex-col gap-2 items-end pointer-events-none">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`pointer-events-auto flex items-center gap-3 bg-white border shadow-lg rounded-xl px-4 py-3 text-sm font-medium text-gray-800 max-w-sm animate-slide-up ${STYLES[t.type]}`}
        >
          {ICONS[t.type]}
          <span className="flex-1">{t.msg}</span>
          <button
            onClick={() => setToasts((prev) => prev.filter((x) => x.id !== t.id))}
            className="text-gray-300 hover:text-gray-500 transition-colors ml-1"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
}

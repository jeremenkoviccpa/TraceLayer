/** Fire a toast from anywhere — no context threading needed. */
export function toast(msg: string, type: "success" | "error" | "info" = "success") {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent("app-toast", { detail: { msg, type } }));
}

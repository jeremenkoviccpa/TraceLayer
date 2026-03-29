"use client";

import { useEffect } from "react";

const TOUR_KEY = "tl_tour_done";

/**
 * First-run product tour using driver.js.
 * Fires automatically once per browser (localStorage flag).
 * Add id="tour-*" attributes on elements you want highlighted.
 */
export default function AppTour() {
  useEffect(() => {
    if (typeof window === "undefined") return;
    const forceTour = sessionStorage.getItem("tl_show_tour") === "1";
    if (!forceTour && localStorage.getItem(TOUR_KEY) === "1") return;
    sessionStorage.removeItem("tl_show_tour");

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let driverObj: any;

    const start = async () => {
      const { driver } = await import("driver.js");

      driverObj = driver({
        showProgress: true,
        progressText: "{{current}} / {{total}}",
        nextBtnText: "Next →",
        prevBtnText: "← Back",
        doneBtnText: "Got it ✓",
        popoverClass: "tl-tour-popover",
        onDestroyStarted: () => {
          localStorage.setItem(TOUR_KEY, "1");
          driverObj.destroy();
        },
        steps: [
          {
            popover: {
              title: "Welcome to TraceLayer 👋",
              description:
                "You're a few minutes away from having a living compliance program. Let's take a quick tour — you can skip at any time.",
              side: "over",
            },
          },
          {
            element: "#tour-score",
            popover: {
              title: "Your compliance score",
              description:
                "This shows how audit-ready you are right now, calculated across your active framework controls. It updates automatically as you connect integrations and collect evidence.",
              side: "bottom",
              align: "start",
            },
          },
          {
            element: "#tour-nav-compliance",
            popover: {
              title: "Step 1 — Scope & Setup",
              description:
                "Start here. Connect an <b>Integration</b> (GitHub, AWS, Google Workspace, Slack…) and we automatically pull your security configurations as evidence. Use <b>Applicability</b> to declare which controls apply to your company.",
              side: "right",
              align: "start",
            },
          },
          {
            element: "#tour-nav-risk",
            popover: {
              title: "Steps 4 — Risk & Security",
              description:
                "Manage your <b>Risk Register</b>, track <b>Incidents</b>, log <b>Vulnerabilities</b>, and record <b>Pen Tests</b>. TraceLayer flags gaps automatically so you don't have to hunt for them manually.",
              side: "right",
              align: "start",
            },
          },
          {
            popover: {
              title: "Operations, People & Privacy",
              description:
                "Steps 5–7 cover your full compliance surface: <b>Asset Inventory</b>, <b>Device Monitoring</b>, <b>Access Reviews</b>, <b>Vendor Risk</b>, <b>Training</b>, <b>Offboarding</b>, <b>Data Flows</b>, <b>RoPA</b>, and <b>Subject Requests</b> — everything auditors look for.",
              side: "over",
            },
          },
          {
            popover: {
              title: "Step 8 — AI Governance",
              description:
                "If you use AI models in your product, complete the <b>AI Questionnaire</b>, generate an <b>AI Audit Package</b>, and monitor your AI agents — all in one place.",
              side: "over",
            },
          },
          {
            element: "#tour-nav-reporting",
            popover: {
              title: "Audit & Reports",
              description:
                "Generate <b>PDF compliance reports</b> for any framework when you're ready for an audit. Run <b>Management Reviews</b>, and share access with your auditor via the <b>Auditor Portal</b> — no email chains needed.",
              side: "right",
              align: "start",
            },
          },
          {
            popover: {
              title: "You're all set — start here",
              description:
                "Go to <b>Integrations</b> under Scope & Setup and connect your first tool. It takes 2 minutes and immediately populates your evidence library and compliance score.",
              side: "over",
            },
          },
        ],
      });

      driverObj.drive();
    };

    // Give the page time to fully render before starting
    const timer = setTimeout(start, 1000);

    return () => {
      clearTimeout(timer);
      driverObj?.destroy();
    };
  }, []);

  return null;
}

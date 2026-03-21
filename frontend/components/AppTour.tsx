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
    if (localStorage.getItem(TOUR_KEY) === "1") return;

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
                "You're 60 seconds away from understanding how compliance evidence works. Let's take a quick tour — you can skip at any time.",
              side: "over",
            },
          },
          {
            element: "#tour-score",
            popover: {
              title: "Your compliance score",
              description:
                "This tells you how audit-ready you are right now, calculated across ~60 SOC 2 controls. The closer to 100%, the better. It updates automatically as you connect your tools.",
              side: "bottom",
              align: "start",
            },
          },
          {
            element: "#tour-nav-compliance",
            popover: {
              title: "The core compliance loop",
              description:
                "Start by connecting an <b>Integration</b> (GitHub, AWS, Google Workspace…). We pull your security configs automatically. Those become <b>Evidence</b> — the proof auditors need to see. <b>Controls</b> shows which requirements are covered.",
              side: "right",
              align: "start",
            },
          },
          {
            element: "#tour-nav-risk",
            popover: {
              title: "Auto-detected security gaps",
              description:
                "Every night we scan your data and flag issues: open critical vulnerabilities, stale vendor reviews, no recent pen test. They show up here as <b>Risks</b> and <b>Incidents</b> — no manual hunting needed.",
              side: "right",
              align: "start",
            },
          },
          {
            element: "#tour-nav-reporting",
            popover: {
              title: "Share proof with the world",
              description:
                "Generate a <b>PDF audit report</b> covering all your evidence when you're ready for SOC 2. Or share your <b>public Trust Page</b> — a live security posture link you send to enterprise customers who ask 'are you SOC 2 compliant?'",
              side: "right",
              align: "start",
            },
          },
          {
            popover: {
              title: "You're set — start here",
              description:
                "Connect your first integration in <b>Integrations</b>. It takes 2 minutes and immediately populates your evidence and compliance score.",
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

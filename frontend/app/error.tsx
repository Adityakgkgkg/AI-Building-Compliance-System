/**
 * Global Error Boundary
 *
 * Catches unhandled errors and displays a user-friendly error page.
 */

"use client";

import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Application error:", error);
  }, [error]);

  return (
    <div className="page-container flex items-center justify-center min-h-screen">
      <div className="text-center section-container">
        {/* Icon */}
        <div
          className="w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-6 animate-pulse-glow"
          style={{
            background: "rgba(239, 68, 68, 0.1)",
            border: "1px solid rgba(239, 68, 68, 0.2)",
          }}
        >
          <svg
            width="36"
            height="36"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#ef4444"
            strokeWidth="1.5"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        </div>

        <h1
          className="text-2xl font-bold mb-3"
          style={{ color: "var(--text-primary)" }}
        >
          Something Went Wrong
        </h1>

        <p
          className="text-base mb-8 max-w-md mx-auto"
          style={{ color: "var(--text-muted)" }}
        >
          An unexpected error occurred. Please try again or contact support if
          the problem persists.
        </p>

        <button onClick={reset} className="btn-primary">
          Try Again
        </button>
      </div>
    </div>
  );
}

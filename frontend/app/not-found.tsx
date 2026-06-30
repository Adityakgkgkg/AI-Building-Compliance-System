/**
 * 404 — Not Found Page
 */

import Link from "next/link";

export default function NotFound() {
  return (
    <div className="page-container flex items-center justify-center min-h-screen">
      <div className="text-center section-container">
        {/* Large 404 */}
        <h1
          className="text-8xl sm:text-9xl font-black mb-4 gradient-text animate-fade-in"
          style={{ lineHeight: 1 }}
        >
          404
        </h1>

        <h2
          className="text-2xl font-bold mb-4 animate-fade-in-up delay-100 opacity-0"
          style={{ color: "var(--text-primary)", animationFillMode: "forwards" }}
        >
          Page Not Found
        </h2>

        <p
          className="text-base mb-8 max-w-md mx-auto animate-fade-in-up delay-200 opacity-0"
          style={{ color: "var(--text-muted)", animationFillMode: "forwards" }}
        >
          The page you&apos;re looking for doesn&apos;t exist or has been moved.
          Let&apos;s get you back on track.
        </p>

        <div className="flex items-center justify-center gap-4 animate-fade-in-up delay-300 opacity-0" style={{ animationFillMode: "forwards" }}>
          <Link href="/" className="btn-primary">
            Go Home
          </Link>
          <Link href="/upload" className="btn-secondary">
            Upload a Plan
          </Link>
        </div>
      </div>
    </div>
  );
}

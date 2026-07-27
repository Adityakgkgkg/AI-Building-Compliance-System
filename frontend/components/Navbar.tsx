/**
 * Navbar Component
 *
 * Responsive navigation bar with glassmorphism effect.
 * Fixed to the top of the viewport.
 */

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const navLinks = [
  { href: "/", label: "Home" },
  { href: "/upload", label: "Upload" },
  { href: "/parser", label: "Parser ⚡" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/about", label: "About" },
];

export default function Navbar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav
      className="fixed top-0 left-0 right-0 z-50 glass"
      style={{
        background: "rgba(10, 14, 26, 0.85)",
        borderBottom: "1px solid var(--border-subtle)",
      }}
    >
      <div className="section-container">
        <div className="flex items-center justify-between h-16">
          {/* ── Logo ────────────────────────────────────────── */}
          <Link href="/" className="flex items-center gap-3 group">
            <div
              className="w-9 h-9 rounded-lg flex items-center justify-center text-white font-bold text-sm"
              style={{ background: "var(--gradient-primary)" }}
            >
              AI
            </div>
            <span className="font-semibold text-sm hidden sm:block" style={{ color: "var(--text-primary)" }}>
              Building Compliance
            </span>
          </Link>

          {/* ── Desktop Links ───────────────────────────────── */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => {
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200"
                  style={{
                    color: isActive ? "var(--accent-purple)" : "var(--text-secondary)",
                    background: isActive ? "rgba(139, 92, 246, 0.1)" : "transparent",
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.color = "var(--text-primary)";
                      e.currentTarget.style.background = "rgba(255,255,255,0.05)";
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.color = "var(--text-secondary)";
                      e.currentTarget.style.background = "transparent";
                    }
                  }}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>

          {/* ── Mobile Menu Button ──────────────────────────── */}
          <button
            className="md:hidden p-2 rounded-lg"
            style={{ color: "var(--text-secondary)" }}
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle navigation menu"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {mobileOpen ? (
                <path d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>

        {/* ── Mobile Menu ────────────────────────────────────── */}
        {mobileOpen && (
          <div
            className="md:hidden pb-4 animate-fade-in"
            style={{ borderTop: "1px solid var(--border-subtle)" }}
          >
            {navLinks.map((link) => {
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className="block px-4 py-3 rounded-lg text-sm font-medium mt-1"
                  style={{
                    color: isActive ? "var(--accent-purple)" : "var(--text-secondary)",
                    background: isActive ? "rgba(139, 92, 246, 0.1)" : "transparent",
                  }}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </nav>
  );
}

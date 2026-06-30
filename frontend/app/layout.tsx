import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

const inter = Inter({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "AI Building Compliance System",
    template: "%s | AI Building Compliance",
  },
  description:
    "AI-Driven Context-Aware System for Automated Building Plan Compliance and 3D Urban Integration. Upload IFC/DXF building plans for automated compliance checking.",
  keywords: [
    "AI",
    "building compliance",
    "IFC",
    "DXF",
    "urban planning",
    "3D",
    "GIS",
    "machine learning",
  ],
  authors: [{ name: "AI Building Compliance Team" }],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">
        <Navbar />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}

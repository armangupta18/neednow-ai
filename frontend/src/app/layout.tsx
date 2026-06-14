import "@/styles/globals.css";
import "@/styles/animations.css";

import type { Metadata } from "next";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";

export const metadata: Metadata = {
  title: "NeedNow AI — Instant Shopping Intelligence",
  description:
    "AI-powered shopping assistant for healthcare and emergency product needs. Situation-to-cart in seconds, powered by Amazon Bedrock.",
  keywords: ["AI shopping", "emergency delivery", "healthcare products", "NeedNow"],
  authors: [{ name: "NeedNow AI Team" }],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#0f172a" />
      </head>
      <body className="flex min-h-screen flex-col antialiased">
        {/* Header */}
        <Header />

        {/* Main content */}
        <main className="flex-1">{children}</main>

        {/* Footer */}
        <Footer />
      </body>
    </html>
  );
}

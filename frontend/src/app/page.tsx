"use client";

import Link from "next/link";
import { ROUTES } from "@/constants/routes";

export default function HomePage() {
  return (
    <div className="flex flex-col">
      {/* ════════════════════════════════════════════════════════
          Hero Section
         ════════════════════════════════════════════════════════ */}
      <section className="relative overflow-hidden bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
        <div className="mx-auto max-w-6xl px-6 py-24 md:py-32 lg:py-40">
          <div className="max-w-3xl">
            <span className="mb-4 inline-block rounded-full bg-blue-500/20 px-4 py-1.5 text-sm font-medium text-blue-300">
              HackOn with Amazon 6.0
            </span>

            <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl lg:text-6xl">
              Describe your situation.
              <br />
              <span className="text-blue-400">Get what you need.</span>
            </h1>

            <p className="mt-6 max-w-xl text-lg text-slate-300 leading-relaxed">
              NeedNow AI transforms urgent situations into instant product
              recommendations. From medical emergencies to last-minute gatherings
              — just describe what&apos;s happening.
            </p>

            <div className="mt-10 flex flex-wrap gap-4">
              <Link
                href={ROUTES.CHAT}
                className="rounded-lg bg-blue-500 px-6 py-3 text-base font-semibold text-white shadow-lg transition hover:bg-blue-600 hover:shadow-xl"
              >
                Start Shopping →
              </Link>
              <Link
                href={ROUTES.EMERGENCY}
                className="rounded-lg border border-red-400/50 bg-red-500/10 px-6 py-3 text-base font-semibold text-red-300 transition hover:bg-red-500/20"
              >
                🚨 Emergency Mode
              </Link>
            </div>
          </div>
        </div>

        {/* Background decoration */}
        <div className="absolute -right-32 -top-32 h-96 w-96 rounded-full bg-blue-500/10 blur-3xl" />
        <div className="absolute -bottom-20 -left-20 h-72 w-72 rounded-full bg-purple-500/10 blur-3xl" />
      </section>

      {/* ════════════════════════════════════════════════════════
          Features Section
         ════════════════════════════════════════════════════════ */}
      <section className="bg-white py-20 lg:py-28">
        <div className="mx-auto max-w-6xl px-6">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-slate-900 sm:text-4xl">
              How NeedNow AI Works
            </h2>
            <p className="mt-4 text-lg text-slate-500">
              Six intelligent agents working together to understand your needs.
            </p>
          </div>

          <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((feature) => (
              <FeatureCard key={feature.title} {...feature} />
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════════
          CTA Section
         ════════════════════════════════════════════════════════ */}
      <section className="border-t bg-slate-50 py-20">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <h2 className="text-3xl font-bold text-slate-900 sm:text-4xl">
            Ready to experience AI-powered shopping?
          </h2>
          <p className="mt-4 text-lg text-slate-500">
            Just tell us your situation — we handle the rest. Voice, text, or emergency mode.
          </p>

          <div className="mt-10 flex flex-wrap justify-center gap-4">
            <Link
              href={ROUTES.CHAT}
              className="rounded-lg bg-slate-900 px-8 py-4 text-base font-semibold text-white shadow-md transition hover:bg-slate-800"
            >
              Try NeedNow AI
            </Link>
            <Link
              href={ROUTES.SUSTAINABILITY}
              className="rounded-lg border border-green-300 bg-green-50 px-8 py-4 text-base font-semibold text-green-700 transition hover:bg-green-100"
            >
              🌱 Sustainability Dashboard
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}

/* ──────────────────────────────────────────────────────────── */

interface Feature {
  icon: string;
  title: string;
  description: string;
}

const FEATURES: Feature[] = [
  {
    icon: "🧠",
    title: "Intent Detection",
    description:
      "Understands what you need from natural language — category, urgency, budget, and more.",
  },
  {
    icon: "⚡",
    title: "Urgency Scoring",
    description:
      "Detects critical needs and prioritizes emergency deliveries automatically.",
  },
  {
    icon: "🛒",
    title: "Smart Recommendations",
    description:
      "Ranks 60,000+ products using semantic search and your personal preferences.",
  },
  {
    icon: "🌱",
    title: "Sustainability Scoring",
    description:
      "Every recommendation comes with eco-friendly alternatives and carbon savings.",
  },
  {
    icon: "🎙️",
    title: "Voice Commerce",
    description:
      "Speak your situation — NeedNow AI transcribes and processes in real-time.",
  },
  {
    icon: "🧬",
    title: "Memory Engine",
    description:
      "Learns your preferences, purchase patterns, and health needs over time.",
  },
];

function FeatureCard({ icon, title, description }: Feature) {
  return (
    <div className="group rounded-xl border border-slate-200 bg-white p-6 shadow-sm transition hover:border-blue-200 hover:shadow-md">
      <span className="text-3xl">{icon}</span>
      <h3 className="mt-4 text-lg font-semibold text-slate-900">{title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-slate-500">{description}</p>
    </div>
  );
}

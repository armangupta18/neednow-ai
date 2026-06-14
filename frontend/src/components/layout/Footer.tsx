import Link from "next/link";
import { ROUTES } from "@/constants/routes";

export default function Footer() {
  return (
    <footer className="border-t bg-slate-50">
      <div className="mx-auto max-w-6xl px-6 py-8">
        <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
          {/* Branding */}
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded bg-slate-900 text-xs font-bold text-white">
              N
            </span>
            <span className="text-sm font-medium text-slate-700">
              NeedNow AI
            </span>
          </div>

          {/* Links */}
          <nav className="flex flex-wrap gap-4 text-sm text-slate-500">
            <Link href={ROUTES.CHAT} className="hover:text-slate-700 transition">Chat</Link>
            <Link href={ROUTES.SUSTAINABILITY} className="hover:text-slate-700 transition">Sustainability</Link>
            <Link href={ROUTES.MEMORY} className="hover:text-slate-700 transition">Memory</Link>
            <Link href={ROUTES.PROFILE} className="hover:text-slate-700 transition">Profile</Link>
          </nav>

          {/* Attribution */}
          <p className="text-xs text-slate-400">
            Powered by Google Gemini • HackOn 6.0
          </p>
        </div>
      </div>
    </footer>
  );
}

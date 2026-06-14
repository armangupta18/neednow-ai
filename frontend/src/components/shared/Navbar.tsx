"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export interface NavItem {
  label: string;
  href: string;
  icon?: string;
}

interface NavbarProps {
  brand?: string;
  items: NavItem[];
  actionLabel?: string;
  actionHref?: string;
  actionVariant?: "primary" | "danger";
}

export default function Navbar({
  brand = "NeedNow AI",
  items,
  actionLabel,
  actionHref,
  actionVariant = "primary",
}: NavbarProps) {
  const pathname = usePathname();

  const actionStyles =
    actionVariant === "danger"
      ? "bg-red-500 text-white hover:bg-red-600"
      : "bg-slate-900 text-white hover:bg-slate-800";

  return (
    <header className="sticky top-0 z-50 border-b bg-white/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-900 text-sm font-bold text-white">
            {brand.charAt(0)}
          </span>
          <span className="text-lg font-bold text-slate-900 hidden sm:inline">{brand}</span>
        </Link>

        {/* Navigation links */}
        <nav className="hidden items-center gap-1 md:flex">
          {items.map(({ label, href, icon }) => {
            const isActive = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium transition ${
                  isActive
                    ? "bg-slate-100 text-slate-900"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                }`}
              >
                {icon && <span>{icon}</span>}
                {label}
              </Link>
            );
          })}
        </nav>

        {/* Action button */}
        {actionLabel && actionHref && (
          <Link
            href={actionHref}
            className={`rounded-lg px-4 py-2 text-sm font-semibold shadow-sm transition ${actionStyles}`}
          >
            {actionLabel}
          </Link>
        )}
      </div>
    </header>
  );
}

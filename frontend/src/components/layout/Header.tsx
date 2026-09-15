"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ROUTES } from "@/constants/routes";
import { useCartStore, selectCartItemCount } from "@/stores/cart.store";

const NAV_ITEMS = [
  { label: "Home", href: ROUTES.HOME },
  { label: "Chat", href: ROUTES.CHAT },
  { label: "Cart", href: ROUTES.CART },
  { label: "Sustainability", href: ROUTES.SUSTAINABILITY },
  { label: "History", href: ROUTES.HISTORY },
];

export default function Header() {
  const pathname = usePathname();
  const rawItemCount = useCartStore(selectCartItemCount);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const itemCount = mounted ? rawItemCount : 0;

  return (
    <header className="sticky top-0 z-50 border-b bg-white/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-900 text-sm font-bold text-white shadow-sm">
            N
          </span>
          <span className="text-lg font-bold text-slate-900">NeedNow AI</span>
        </Link>

        {/* Navigation */}
        <nav className="hidden items-center gap-1 md:flex">
          {NAV_ITEMS.map(({ label, href }) => {
            const isActive = pathname === href;
            const isCart = label === "Cart";

            return (
              <Link
                key={href}
                href={href}
                className={`inline-flex items-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium transition ${
                  isActive
                    ? "bg-slate-100 text-slate-900"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                }`}
              >
                <span>{label}</span>
                {isCart && itemCount > 0 && (
                  <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-emerald-600 px-1.5 text-[11px] font-bold text-white shadow-sm animate-scale-in">
                    {itemCount}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Emergency Button */}
        <Link
          href={ROUTES.EMERGENCY}
          className="rounded-lg bg-red-500 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-red-600 active:scale-95"
        >
          🚨 Emergency
        </Link>
      </div>
    </header>
  );
}

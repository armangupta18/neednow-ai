import Link from "next/link";

export interface FooterLink {
  label: string;
  href: string;
}

interface FooterProps {
  brand?: string;
  links?: FooterLink[];
  attribution?: string;
}

export default function Footer({
  brand = "NeedNow AI",
  links = [],
  attribution = "Powered by Amazon Bedrock • HackOn 6.0",
}: FooterProps) {
  return (
    <footer className="border-t bg-slate-50">
      <div className="mx-auto max-w-6xl px-6 py-8">
        <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
          {/* Brand */}
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded bg-slate-900 text-xs font-bold text-white">
              {brand.charAt(0)}
            </span>
            <span className="text-sm font-medium text-slate-700">{brand}</span>
          </div>

          {/* Links */}
          {links.length > 0 && (
            <nav className="flex flex-wrap gap-4 text-sm text-slate-500">
              {links.map(({ label, href }) => (
                <Link
                  key={href}
                  href={href}
                  className="transition hover:text-slate-700"
                >
                  {label}
                </Link>
              ))}
            </nav>
          )}

          {/* Attribution */}
          <p className="text-xs text-slate-400">{attribution}</p>
        </div>
      </div>
    </footer>
  );
}

import { ReactNode } from "react";

interface SectionProps {
  children: ReactNode;
  /** Section title */
  title?: string;
  /** Section subtitle */
  subtitle?: string;
  /** Background variant */
  variant?: "default" | "muted" | "dark";
  /** Additional className */
  className?: string;
  /** Center the title/subtitle */
  centered?: boolean;
}

const variantStyles = {
  default: "bg-white",
  muted: "bg-slate-50 border-t border-b",
  dark: "bg-slate-900 text-white",
};

export default function Section({
  children,
  title,
  subtitle,
  variant = "default",
  className = "",
  centered = false,
}: SectionProps) {
  return (
    <section className={`py-12 lg:py-16 ${variantStyles[variant]} ${className}`}>
      <div className="mx-auto max-w-6xl px-6">
        {/* Header */}
        {(title || subtitle) && (
          <div className={`mb-10 ${centered ? "text-center" : ""}`}>
            {title && (
              <h2
                className={`text-2xl font-bold sm:text-3xl ${
                  variant === "dark" ? "text-white" : "text-slate-900"
                }`}
              >
                {title}
              </h2>
            )}
            {subtitle && (
              <p
                className={`mt-3 text-base ${
                  variant === "dark" ? "text-slate-300" : "text-slate-500"
                }`}
              >
                {subtitle}
              </p>
            )}
          </div>
        )}

        {/* Content */}
        {children}
      </div>
    </section>
  );
}

import { ReactNode } from "react";

interface EmptyStateProps {
  /** Emoji or icon */
  icon?: string | ReactNode;
  /** Main title */
  title: string;
  /** Description text */
  description?: string;
  /** Action button label */
  actionLabel?: string;
  /** Action callback */
  onAction?: () => void;
  /** Additional className */
  className?: string;
  /** Compact mode */
  compact?: boolean;
}

export default function EmptyState({
  icon = "📦",
  title,
  description,
  actionLabel,
  onAction,
  className = "",
  compact = false,
}: EmptyStateProps) {
  return (
    <div
      className={`flex flex-col items-center text-center ${
        compact ? "py-8" : "py-16"
      } ${className}`}
    >
      {/* Icon */}
      <span className={compact ? "text-3xl mb-3" : "text-5xl mb-4"}>
        {icon}
      </span>

      {/* Title */}
      <h3
        className={`font-semibold text-slate-700 ${
          compact ? "text-base" : "text-lg"
        }`}
      >
        {title}
      </h3>

      {/* Description */}
      {description && (
        <p
          className={`mt-1.5 max-w-xs text-slate-500 ${
            compact ? "text-xs" : "text-sm"
          }`}
        >
          {description}
        </p>
      )}

      {/* Action button */}
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className={`mt-5 rounded-lg border border-slate-300 font-medium text-slate-700 transition hover:bg-slate-50 ${
            compact ? "px-3 py-1.5 text-xs" : "px-4 py-2 text-sm"
          }`}
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}

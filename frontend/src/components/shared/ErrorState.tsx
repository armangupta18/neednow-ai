interface ErrorStateProps {
  /** Main error title */
  title?: string;
  /** Error description or message */
  message?: string;
  /** Retry callback */
  onRetry?: () => void;
  /** Retry button label */
  retryLabel?: string;
  /** Additional className */
  className?: string;
  /** Compact mode (inline vs. full page) */
  compact?: boolean;
}

export default function ErrorState({
  title = "Something went wrong",
  message = "We encountered an unexpected error. Please try again.",
  onRetry,
  retryLabel = "Try Again",
  className = "",
  compact = false,
}: ErrorStateProps) {
  return (
    <div
      className={`flex flex-col items-center text-center ${
        compact ? "py-6" : "py-16"
      } ${className}`}
    >
      {/* Icon */}
      <div
        className={`flex items-center justify-center rounded-full bg-red-100 ${
          compact ? "h-10 w-10 mb-3" : "h-14 w-14 mb-4"
        }`}
      >
        <svg
          className={`text-red-500 ${compact ? "h-5 w-5" : "h-7 w-7"}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.07 16.5c-.77.833.192 2.5 1.732 2.5z"
          />
        </svg>
      </div>

      {/* Title */}
      <h3
        className={`font-semibold text-slate-900 ${
          compact ? "text-base" : "text-xl"
        }`}
      >
        {title}
      </h3>

      {/* Message */}
      <p
        className={`mt-2 max-w-sm text-slate-500 ${
          compact ? "text-xs" : "text-sm"
        }`}
      >
        {message}
      </p>

      {/* Retry button */}
      {onRetry && (
        <button
          onClick={onRetry}
          className={`mt-4 rounded-lg bg-slate-900 font-semibold text-white shadow transition hover:bg-slate-800 ${
            compact ? "px-3 py-1.5 text-xs" : "px-5 py-2.5 text-sm"
          }`}
        >
          {retryLabel}
        </button>
      )}
    </div>
  );
}

interface LoadingSpinnerProps {
  /** Size variant */
  size?: "xs" | "sm" | "md" | "lg" | "xl";
  /** Color variant */
  color?: "default" | "primary" | "white";
  /** Optional label for accessibility */
  label?: string;
  /** Show label text below spinner */
  showLabel?: boolean;
  /** Additional className */
  className?: string;
}

const sizeMap = {
  xs: "h-3 w-3 border",
  sm: "h-4 w-4 border-2",
  md: "h-6 w-6 border-2",
  lg: "h-10 w-10 border-2",
  xl: "h-14 w-14 border-3",
};

const colorMap = {
  default: "border-slate-300 border-t-slate-900",
  primary: "border-blue-200 border-t-blue-600",
  white: "border-white/30 border-t-white",
};

export default function LoadingSpinner({
  size = "md",
  color = "default",
  label = "Loading",
  showLabel = false,
  className = "",
}: LoadingSpinnerProps) {
  return (
    <div
      className={`inline-flex flex-col items-center gap-2 ${className}`}
      role="status"
      aria-label={label}
    >
      <div
        className={`animate-spin rounded-full ${sizeMap[size]} ${colorMap[color]}`}
      />
      {showLabel && (
        <span className="text-xs text-slate-500">{label}</span>
      )}
      <span className="sr-only">{label}</span>
    </div>
  );
}

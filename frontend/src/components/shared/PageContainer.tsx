import { ReactNode } from "react";

interface PageContainerProps {
  children: ReactNode;
  /** Maximum width variant */
  maxWidth?: "sm" | "md" | "lg" | "xl" | "full";
  /** Additional className */
  className?: string;
  /** Padding override */
  padded?: boolean;
}

const maxWidthMap = {
  sm: "max-w-2xl",
  md: "max-w-4xl",
  lg: "max-w-6xl",
  xl: "max-w-7xl",
  full: "max-w-full",
};

export default function PageContainer({
  children,
  maxWidth = "lg",
  className = "",
  padded = true,
}: PageContainerProps) {
  return (
    <div
      className={`mx-auto w-full ${maxWidthMap[maxWidth]} ${
        padded ? "px-4 py-6 sm:px-6 lg:px-8" : ""
      } ${className}`}
    >
      {children}
    </div>
  );
}

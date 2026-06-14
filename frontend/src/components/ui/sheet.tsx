"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface SheetProps {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
  side?: "left" | "right" | "top" | "bottom";
}

const sideStyles: Record<string, string> = {
  left: "inset-y-0 left-0 w-80 border-r animate-slide-in-right [animation-direction:reverse]",
  right: "inset-y-0 right-0 w-80 border-l animate-slide-in-right",
  top: "inset-x-0 top-0 h-80 border-b animate-fade-in",
  bottom: "inset-x-0 bottom-0 h-80 border-t animate-slide-in-bottom",
};

function Sheet({ open, onClose, children, side = "right" }: SheetProps) {
  React.useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (open) {
      document.addEventListener("keydown", handleEsc);
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.removeEventListener("keydown", handleEsc);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      data-slot="sheet"
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 animate-fade-in"
        onClick={onClose}
        aria-hidden="true"
      />
      {/* Panel */}
      <div
        className={cn(
          "fixed flex flex-col bg-card shadow-xl",
          sideStyles[side]
        )}
      >
        {children}
      </div>
    </div>
  );
}

function SheetHeader({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="sheet-header"
      className={cn("flex flex-col gap-1.5 p-6 pb-0", className)}
      {...props}
    />
  );
}

function SheetTitle({ className, ...props }: React.ComponentProps<"h2">) {
  return (
    <h2
      data-slot="sheet-title"
      className={cn("text-lg font-semibold leading-none tracking-tight", className)}
      {...props}
    />
  );
}

function SheetDescription({ className, ...props }: React.ComponentProps<"p">) {
  return (
    <p
      data-slot="sheet-description"
      className={cn("text-sm text-muted-foreground", className)}
      {...props}
    />
  );
}

function SheetContent({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="sheet-content"
      className={cn("flex-1 overflow-y-auto p-6", className)}
      {...props}
    />
  );
}

function SheetFooter({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="sheet-footer"
      className={cn(
        "flex items-center justify-end gap-2 border-t p-6",
        className
      )}
      {...props}
    />
  );
}

export {
  Sheet,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetContent,
  SheetFooter,
};

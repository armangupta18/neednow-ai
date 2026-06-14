import * as React from "react";
import { cn } from "@/lib/utils";

function Textarea({
  className,
  ...props
}: React.ComponentProps<"textarea">) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        "flex min-h-[80px] w-full rounded-lg border border-border bg-transparent px-3 py-2 text-sm shadow-sm outline-none transition",
        "placeholder:text-muted-foreground",
        "focus:border-ring focus:ring-3 focus:ring-ring/20",
        "disabled:cursor-not-allowed disabled:opacity-50",
        "aria-invalid:border-red-500 aria-invalid:ring-red-500/20",
        "resize-y",
        className
      )}
      {...props}
    />
  );
}

export { Textarea };

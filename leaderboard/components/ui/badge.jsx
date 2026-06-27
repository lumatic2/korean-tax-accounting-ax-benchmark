import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium whitespace-nowrap leading-tight",
  {
    variants: {
      variant: {
        default: "border-border bg-secondary text-secondary-foreground",
        pin: "border-[#cfe0fb] bg-[#eef4ff] text-[#2256b3]",
        ok: "border-[#bce8d0] bg-[#e6f7ee] text-ok",
        error: "border-[#f5c6c2] bg-[#fdecec] text-destructive",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

function Badge({ className, variant, ...props }) {
  return (
    <span className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };

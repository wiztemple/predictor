import Link from "next/link";
import { ADS, AD_SLOTS } from "@/lib/ads";

/** A reserved advert space. Shows a quiet "advertise here" placeholder until filled. */
export function AdSlot({ id, className = "" }: { id: string; className?: string }) {
  const slot = AD_SLOTS.find((s) => s.id === id);
  if (!ADS.enabled || !slot) return null;
  const width = slot.size === "wide" ? "max-w-[970px]" : "max-w-[728px]";
  return (
    <aside aria-label="Advertisement" data-ad-slot={id} className={`mx-auto w-full ${width} ${className}`}>
      <p className="mb-1 text-[10px] font-medium tracking-widest text-text-3 uppercase">Advertisement</p>
      <Link
        href="/advertise"
        className="flex h-[100px] flex-col items-center justify-center gap-1 rounded-xl border border-dashed border-border text-center transition-colors hover:border-accent sm:h-[90px]"
      >
        <span className="text-sm font-semibold text-text-2">Your brand here</span>
        <span className="text-xs text-text-3">Ad space available · Advertise with us →</span>
      </Link>
    </aside>
  );
}

import Link from "next/link";

export function PreviewBanner({ status, dataThrough }: { status: string; dataThrough: string }) {
  if (status === "validated") return null;
  return (
    <div className="border-b border-notice-border bg-notice-bg text-notice-text">
      <p className="mx-auto max-w-5xl px-4 py-1.5 text-xs">
        <strong className="font-semibold">Preview.</strong>{" "}
        <span className="hidden sm:inline">In backtests these estimates were less accurate than bookmaker odds; see the </span>
        <span className="sm:hidden">See the </span>
        <Link href="/track-record" className="underline">
          track record
        </Link>
        <span className="hidden sm:inline">. Results data runs to {dataThrough}</span>.
      </p>
    </div>
  );
}

export function Disclaimer() {
  return (
    <p className="text-xs leading-relaxed text-text-3">
      <strong className="font-semibold text-text-2">18+ · Please gamble responsibly.</strong> These are statistical
      estimates from past results, not certainties and not betting advice. A 70% chance still loses about 3 times in
      10, and bookmakers&apos; odds have been more accurate than ours over time. If gambling stops being fun, get help
      at BeGambleAware.org.
    </p>
  );
}

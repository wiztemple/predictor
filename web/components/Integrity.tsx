const AUDIT = "https://github.com/wiztemple/predictor/tree/main/data/picks/audit";
const HISTORY = "https://github.com/wiztemple/predictor/commits/main/data/picks/audit";

/** How the record is kept honest, with links to the public, timestamped files. */
export function Integrity() {
  return (
    <section className="rounded-2xl border border-border bg-surface p-4 text-sm sm:p-5">
      <h2 className="font-bold">How we keep this honest</h2>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-text-2">
        <li>Every pick is saved before its match kicks off, and saved picks are never edited or deleted.</li>
        <li>Each pick is settled automatically from the official result. Losses stay on the record like wins.</li>
        <li>Weekly lists are fixed when they&apos;re picked and don&apos;t change during the week.</li>
        <li>
          The full log of every pick and result is published after each update in our public{" "}
          <a href={AUDIT} className="font-semibold text-accent hover:underline">
            pick log
          </a>
          . Its{" "}
          <a href={HISTORY} className="font-semibold text-accent hover:underline">
            change history
          </a>{" "}
          shows when each pick was published, so anyone can check nothing was added late or removed.
        </li>
      </ul>
    </section>
  );
}

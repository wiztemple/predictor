import type { Metadata, Viewport } from "next";
import Link from "next/link";
import { Geist, Geist_Mono } from "next/font/google";
import { Disclaimer, PreviewBanner } from "@/components/Notices";
import { getPredictions } from "@/lib/predictions";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

// Light theme only: no dark mode, whatever the visitor's device setting.
export const viewport: Viewport = { colorScheme: "light" };

export const metadata: Metadata = {
  title: { default: "MatchPredictor", template: "%s · MatchPredictor" },
  description: "Statistical win/draw/loss estimates for upcoming football matches.",
};

export default async function RootLayout({ children }: LayoutProps<"/">) {
  const doc = await getPredictions();
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <PreviewBanner status={doc.status} dataThrough={doc.data_through} />
        <header className="border-b border-border bg-surface text-text">
          <nav className="mx-auto flex max-w-5xl flex-col gap-2 px-4 py-3 text-sm sm:flex-row sm:items-center">
            <Link href="/" className="mr-3 flex items-center gap-2 text-base font-extrabold tracking-tight">
              {/* Panenka mark: the chipped penalty's dotted arc */}
              <svg aria-hidden viewBox="0 0 48 48" className="size-7">
                <path d="M7 41 Q20 0 37 22" fill="none" stroke="var(--text)" strokeWidth="3.6" strokeLinecap="round" strokeDasharray="0.1 6.4" />
                <circle cx="37.5" cy="25" r="6.5" fill="var(--accent)" />
                <line x1="4" y1="44" x2="44" y2="44" stroke="var(--text)" strokeWidth="3.6" strokeLinecap="round" />
              </svg>
              MatchPredictor
            </Link>
            <div className="-mx-1 flex gap-1 overflow-x-auto sm:ml-auto">
            {[
              ["/", "Matches"],
              ["/picks", "Picks"],
              ["/weekly", "Weekly 10s"],
              ["/leagues", "Leagues"],
              ["/track-record", "Track record"],
            ].map(([href, label]) => (
              <Link
                key={href}
                href={href}
                className="shrink-0 rounded-full px-3 py-1.5 font-medium whitespace-nowrap text-text-2 transition-colors hover:bg-surface-2 hover:text-text"
              >
                {label}
              </Link>
            ))}
            </div>
          </nav>
        </header>
        <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8">{children}</main>
        <footer className="border-t border-border bg-surface">
          <div className="mx-auto max-w-5xl px-4 py-6">
            <Disclaimer />
          </div>
        </footer>
      </body>
    </html>
  );
}

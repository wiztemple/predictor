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
  title: { default: "Match Probabilities", template: "%s · Match Probabilities" },
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
              <svg aria-hidden viewBox="0 0 24 24" className="size-7 drop-shadow">
                <circle cx="12" cy="12" r="11" fill="var(--text)" />
                <path
                  fill="var(--surface)"
                  d="M12 6.2l3.4 2.5-1.3 4h-4.2l-1.3-4zM5 9.6l2.2-.5 1.4 4.1-1.6 2.3-2.1-.7A8.6 8.6 0 015 9.6zm14 0a8.6 8.6 0 01.1 5.2l-2.1.7-1.6-2.3 1.4-4.1zM9.6 18.7l.9-2.4h3l.9 2.4a8.6 8.6 0 01-4.8 0z"
                />
              </svg>
              Match Probabilities
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

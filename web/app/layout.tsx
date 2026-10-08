import type { Metadata } from "next";
import Link from "next/link";
import { Geist, Geist_Mono } from "next/font/google";
import { Disclaimer, PreviewBanner } from "@/components/Notices";
import { getPredictions } from "@/lib/predictions";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

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
        <header className="border-b border-border">
          <nav className="mx-auto flex max-w-5xl flex-wrap items-center gap-x-5 gap-y-2 px-4 py-3 text-sm">
            <Link href="/" className="mr-2 text-base font-bold tracking-tight text-text">
              Match Probabilities
            </Link>
            <Link href="/" className="text-text-2 hover:text-text sm:ml-auto">
              Matches
            </Link>
            <Link href="/picks" className="text-text-2 hover:text-text">
              Picks
            </Link>
            <Link href="/leagues" className="text-text-2 hover:text-text">
              Leagues
            </Link>
            <Link href="/track-record" className="text-text-2 hover:text-text">
              Track record
            </Link>
          </nav>
        </header>
        <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8">{children}</main>
        <footer className="border-t border-border">
          <div className="mx-auto max-w-5xl px-4 py-6">
            <Disclaimer />
          </div>
        </footer>
      </body>
    </html>
  );
}

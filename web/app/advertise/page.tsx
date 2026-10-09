import type { Metadata } from "next";
import { ADS, AD_SIZES, AD_SLOTS } from "@/lib/ads";

export const metadata: Metadata = { title: "Advertise" };

export default function Advertise() {
  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight sm:text-3xl">Advertise with us</h1>
        <p className="mt-2 text-text-2">
          Reach football fans checking match probabilities, daily picks and weekly top 10s across 21 leagues. These
          are the spaces available.
        </p>
      </div>
      <div className="overflow-x-auto rounded-xl border border-border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs text-text-3 uppercase">
              <th className="px-4 py-2 font-medium">Placement</th>
              <th className="px-4 py-2 font-medium">Size</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {AD_SLOTS.map((s) => (
              <tr key={s.id}>
                <td className="px-4 py-3">{s.where}</td>
                <td className="px-4 py-3 whitespace-nowrap text-text-2 tabular">{AD_SIZES[s.size]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="rounded-xl border border-border p-4">
        <h2 className="font-bold">Get in touch</h2>
        {ADS.contact ? (
          <p className="mt-1 text-text-2">
            Contact <span className="font-semibold text-text select-all">{ADS.contact}</span> for rates and availability.
          </p>
        ) : (
          <p className="mt-1 text-text-2">Contact details are coming soon.</p>
        )}
        <p className="mt-3 text-xs text-text-3">
          Ads must be for adults only and follow responsible-gambling rules. We don&apos;t run ads that promise sure
          wins or &quot;fixed&quot; matches.
        </p>
      </div>
    </div>
  );
}

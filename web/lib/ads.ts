/** Advert placements. Set `contact` to an email or link to show it on every slot;
 *  set `enabled: false` to hide all slots. To run a real ad, drop its markup into
 *  the matching slot in components/AdSlot.tsx (keyed by slot id). */
export const ADS = {
  enabled: true,
  contact: "", // e.g. "ads@yourdomain.com" - empty shows "Ad space available" only
};

export type AdSize = "banner" | "wide";

export const AD_SLOTS: { id: string; where: string; size: AdSize }[] = [
  { id: "home-mid", where: "Home page, between the top picks and all matches", size: "banner" },
  { id: "match-mid", where: "Every match page, below the main markets", size: "banner" },
  { id: "picks-mid", where: "Picks page, above the integrity section", size: "banner" },
  { id: "weekly-bottom", where: "Weekly top 10s, below the list", size: "banner" },
  { id: "footer", where: "Every page, above the footer", size: "wide" },
];

export const AD_SIZES: Record<AdSize, string> = {
  banner: "728×90 desktop, 320×100 mobile",
  wide: "970×90 desktop, 320×100 mobile",
};

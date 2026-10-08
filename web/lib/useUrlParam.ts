"use client";

import { useSyncExternalStore } from "react";

// Tiny URL-search-param store: replaceState doesn't fire events, so we notify ourselves.
const listeners = new Set<() => void>();
const subscribe = (cb: () => void) => {
  listeners.add(cb);
  window.addEventListener("popstate", cb);
  return () => {
    listeners.delete(cb);
    window.removeEventListener("popstate", cb);
  };
};

/** Read/write one query parameter without a reload. Server render sees `null`. */
export function useUrlParam(name: string): [string | null, (v: string | null) => void] {
  const search = useSyncExternalStore(subscribe, () => window.location.search, () => "");
  const value = new URLSearchParams(search).get(name);
  const set = (v: string | null) => {
    const url = new URL(window.location.href);
    if (v === null) url.searchParams.delete(name);
    else url.searchParams.set(name, v);
    window.history.replaceState(null, "", url);
    listeners.forEach((l) => l());
  };
  return [value, set];
}

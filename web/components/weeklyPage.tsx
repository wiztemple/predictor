import { WeeklyView } from "@/components/WeeklyView";
import { getPicksBacktest, getWeekly } from "@/lib/picksRecord";

/** Shared body of /weekly and /weekly/[list]. */
export async function weeklyPage(active: string) {
  const [weekly, bt] = await Promise.all([getWeekly(), getPicksBacktest()]);
  const lists = Object.entries(weekly?.lists ?? {}).map(([key, v]) => ({ key, label: v.label }));
  return (
    <WeeklyView lists={lists} active={active} data={weekly?.lists[active]} backtest={bt?.weekly_lists?.[active]} />
  );
}

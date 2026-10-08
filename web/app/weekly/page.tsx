import type { Metadata } from "next";
import { weeklyPage } from "@/components/weeklyPage";

export const metadata: Metadata = { title: "Weekly top 10s" };

export default async function WeeklyPage() {
  return weeklyPage("safe");
}

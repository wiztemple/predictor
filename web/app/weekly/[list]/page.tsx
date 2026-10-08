import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getWeekly } from "@/lib/picksRecord";
import { weeklyPage } from "@/components/weeklyPage";

export async function generateStaticParams() {
  const weekly = await getWeekly();
  return Object.keys(weekly?.lists ?? {}).map((list) => ({ list }));
}

export async function generateMetadata({ params }: PageProps<"/weekly/[list]">): Promise<Metadata> {
  const { list } = await params;
  const weekly = await getWeekly();
  return { title: weekly?.lists[list]?.label ?? "Weekly top 10" };
}

export default async function WeeklyListPage({ params }: PageProps<"/weekly/[list]">) {
  const { list } = await params;
  const weekly = await getWeekly();
  if (!weekly?.lists[list]) notFound();
  return weeklyPage(list);
}

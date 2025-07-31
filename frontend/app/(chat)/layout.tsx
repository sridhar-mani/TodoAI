import { DataStreamProvider } from "@/components/data-stream-provider";

export const experimental_ppr = true;

export default async function Layout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <DataStreamProvider>{children}</DataStreamProvider>;
}

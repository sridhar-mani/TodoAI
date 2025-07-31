import { redirect } from "next/navigation";

export default async function Page(props: { params: Promise<{ id: string }> }) {
  redirect("/");
}

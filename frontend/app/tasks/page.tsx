import { cookies } from "next/headers";
import { DEFAULT_CHAT_MODEL } from "@/lib/ai/models";
import { generateUUID } from "@/lib/utils";
import TaskListPage from "./TaskListPage";

export default async function TasksPage() {
  const id = generateUUID();
  const cookieStore = await cookies();
  const modelIdFromCookie = cookieStore.get("chat-model");
  const chatModel = modelIdFromCookie?.value || DEFAULT_CHAT_MODEL;

  return <TaskListPage id={id} chatModel={chatModel} />;
}

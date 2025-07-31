export interface Task {
  id: number;
  title: string;
  description: string;
  status: "pending" | "in_progress" | "completed" | "failed";
  priority: "low" | "medium" | "high" | "urgent";
  due_date: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessagePart {
  type: "text";
  text: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  parts: ChatMessagePart[];
  attachments?: Attachment[];
}

export interface Attachment {
  id: string;
  type: "image" | "code" | "text" | "sheet";
  content: string;
}

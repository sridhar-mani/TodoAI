"use client";

import { useState } from "react";
import type { ChatMessage, Attachment } from "@/lib/types";
import type { UseChatHelpers } from "@ai-sdk/react";
import { Messages } from "./messages";
import { MultimodalInput } from "./multimodal-input";
import { toast } from "./toast";
import { useChatStore } from "../stores/chat-store";

// Simple UUID generator
function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

interface ChatProps {
  id: string;
  initialMessages: ChatMessage[];
  initialChatModel: string;
  initialVisibilityType: string;
  isReadonly: boolean;
  autoResume: boolean;
}

export function Chat({
  id,
  initialMessages,
  initialChatModel,
  initialVisibilityType,
  isReadonly,
  autoResume,
}: ChatProps) {
  const { messages, isLoading, addMessage, clearMessages, setIsLoading, setMessages } = useChatStore();
  const [input, setInput] = useState<string>("");
  const [attachments, setAttachments] = useState<Attachment[]>([]);

  const sendMessage = async (parts: { type: "text"; text: string }[]) => {
    const userMessage: ChatMessage = {
      id: generateUUID(),
      role: "user",
      parts: parts,
    };

    // Add user message
    addMessage(userMessage);
    setIsLoading(true);

    try {
      // Extract text content
      const messageText = parts
        .filter(part => part.type === "text")
        .map(part => part.text)
        .join(" ");

      // Call backend API
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [...messages, userMessage],
          id: id,
          selectedChatModel: initialChatModel,
          selectedVisibilityType: initialVisibilityType,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      // Read the streaming response
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let assistantContent = "";

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.substring(6));
                if (data.content) {
                  assistantContent += data.content;
                }
              } catch (error) {
                // Ignore parsing errors for incomplete chunks
              }
            }
          }
        }
      }

      // Add assistant response
      const assistantMessage: ChatMessage = {
        id: generateUUID(),
        role: "assistant",
        parts: [{ type: "text", text: assistantContent || "I received your message." }],
      };

      addMessage(assistantMessage);

    } catch (error) {
      console.error("Error sending message:", error);
      toast({ 
        type: "error", 
        description: "Failed to send message. Please try again." 
      });
      
      // Add error message
      const errorMessage: ChatMessage = {
        id: generateUUID(),
        role: "assistant",
        parts: [{ type: "text", text: "Sorry, I'm having trouble processing your request. Please try again." }],
      };
      addMessage(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = async (message: any) => {
    if (message.parts) {
      await sendMessage(message.parts);
    } else if (message.text) {
      await sendMessage([{ type: "text", text: message.text }]);
    }
    setInput("");
  };

  return (
    <div className="flex flex-col min-w-0 h-dvh bg-white dark:bg-black">
      {/* Header */}
      <div className="border-b border-gray-200 dark:border-gray-800 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="size-8 bg-blue-500 rounded-full flex items-center justify-center">
              <svg
                className="size-4 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-semibold text-black dark:text-white">
                AI Assistant
              </h1>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={clearMessages}
              className="p-2 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              aria-label="Clear chat"
              title="Clear chat history"
            >
              <svg
                className="size-5 text-gray-600 dark:text-gray-300"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </button>
            
            <button
              onClick={() => {
                const html = document.documentElement;
                if (html.classList.contains("dark")) {
                  html.classList.remove("dark");
                  localStorage.setItem("theme", "light");
                } else {
                  html.classList.add("dark");
                  localStorage.setItem("theme", "dark");
                }
              }}
              className="p-2 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              aria-label="Toggle theme"
            >
              <svg
                className="size-5 text-gray-600 dark:text-gray-300"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
                  className="dark:hidden"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707"
                  className="hidden dark:block"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-auto relative">
        {messages.length === 0 && !isLoading && (
          <div className="absolute inset-0 flex flex-col items-center justify-center p-8">
            <div className="text-center max-w-md">
              <div className="size-12 bg-blue-500 rounded-full flex items-center justify-center mb-4 mx-auto">
                <svg
                  className="size-6 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-black dark:text-white mb-3">
                How can I help?
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Manage your tasks with simple conversation
              </p>

              <div className="space-y-2 text-left">
                <button
                  onClick={() => {
                    handleSend({ parts: [{ type: "text", text: "Create a task to buy groceries" }] });
                  }}
                  className="w-full border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:bg-gray-50 dark:hover:bg-gray-900/50 transition-colors text-left"
                >
                  <span className="text-gray-700 dark:text-gray-300 text-sm">
                    &quot;Create a task to buy groceries&quot;
                  </span>
                </button>
                <button
                  onClick={() => {
                    handleSend({ parts: [{ type: "text", text: "Show me all my tasks" }] });
                  }}
                  className="w-full border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:bg-gray-50 dark:hover:bg-gray-900/50 transition-colors text-left"
                >
                  <span className="text-gray-700 dark:text-gray-300 text-sm">
                    &quot;Show me all my tasks&quot;
                  </span>
                </button>
              </div>
            </div>
          </div>
        )}

        <Messages
          chatId={id}
          status={(isLoading ? "streaming" : "idle") as UseChatHelpers<ChatMessage>["status"]}
          votes={[]}
          messages={messages}
          setMessages={setMessages}
          regenerate={async () => {}}
          isReadonly={isReadonly}
          isArtifactVisible={false}
        />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 dark:border-gray-800 p-3">
        <div className="max-w-4xl mx-auto">
          {!isReadonly && (
            <MultimodalInput
              chatId={id}
              input={input}
              setInput={setInput}
              status={(isLoading ? "streaming" : "idle") as UseChatHelpers<ChatMessage>["status"]}
              stop={() => {}}
              attachments={attachments}
              setAttachments={setAttachments}
              messages={messages}
              setMessages={setMessages}
              sendMessage={handleSend}
              selectedVisibilityType={initialVisibilityType as any}
            />
          )}
        </div>
      </div>
    </div>
  );
}

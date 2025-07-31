"use client";

import { DefaultChatTransport } from "ai";
import { useChat } from "@ai-sdk/react";
import { useEffect, useState } from "react";
import useSWR, { useSWRConfig } from "swr";

type Vote = {
  id: string;
  value: number;
  messageId: string;
  userId: string;
};
import { fetcher, fetchWithErrorHandlers, generateUUID } from "@/lib/utils";
import { Artifact } from "./artifact";
import { MultimodalInput } from "./multimodal-input";
import { Messages } from "./messages";
import type { VisibilityType } from "./visibility-selector";
import { useArtifactSelector } from "@/hooks/use-artifact";

import { toast } from "./toast";
import { useSearchParams } from "next/navigation";
import { useChatVisibility } from "@/hooks/use-chat-visibility";
import { useAutoResume } from "@/hooks/use-auto-resume";
import { ChatSDKError } from "@/lib/errors";
import type { Attachment, ChatMessage } from "@/lib/types";
import { useDataStream } from "./data-stream-provider";

export function Chat({
  id,
  initialMessages,
  initialChatModel,
  initialVisibilityType,
  isReadonly,
  autoResume,
}: {
  id: string;
  initialMessages: ChatMessage[];
  initialChatModel: string;
  initialVisibilityType: VisibilityType;
  isReadonly: boolean;
  autoResume: boolean;
}) {
  const { data: history = [], error: historyError, mutate: reloadHistory } = useSWR(
    `/api/chat/history`,
    async (url) => {
      try {
        const response = await fetch(url);
        
        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`Error ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        return data;
      } catch (error) {
        throw error;
      }
    }
  );



  const { visibilityType } = useChatVisibility({ chatId: id, initialVisibilityType });
  const { mutate: globalMutate } = useSWRConfig();
  const { setDataStream } = useDataStream();
  const [input, setInput] = useState<string>("");

  const { messages, setMessages, sendMessage, status, stop, regenerate, resumeStream } = useChat<ChatMessage>({
    id:"main_chat",
    messages: history,
    experimental_throttle: 100,
    generateId: generateUUID,
    transport: new DefaultChatTransport({
      api: "/api/chat",
      fetch: fetchWithErrorHandlers,
      prepareSendMessagesRequest({ messages, id, body }) {
        return { 
          body: { 
            messages, 
            id: 'main_chat', 
            selectedChatModel: initialChatModel, 
            selectedVisibilityType: initialVisibilityType,
            ...body 
          } 
        };
      },
    }),
    onData: (dataPart) => {
      setDataStream((ds) => (ds ? [...ds, dataPart] : []));
    },
onFinish: async () => {
      const last = messages.at(-1);
      if (last?.role === "assistant") {
        try {
          const response = await fetch("/api/chat/message", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
              chatId: 'main_chat', 
              id: last.id || generateUUID(),
              role: last.role,
              parts: last.parts,
              timestamp: new Date().toISOString()
            }),
          });
          
          if (!response.ok) {
            const errorText = await response.text();
            console.error(`Error saving message: ${errorText}`);
          }
          
          reloadHistory();
        } catch (error) {
          console.error("Error saving assistant message:", error);
        }
      }
    },


    onError: (error) => {
      if (error instanceof ChatSDKError) {
        toast({ type: "error", description: error.message });
      }
    },
  });

const handleSend = async (parts:any) => {
    const messageId = generateUUID();
    sendMessage({ role: "user", parts });
    
    try {
      const response = await fetch("/api/chat/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          chatId: 'main_chat', 
          id: messageId, 
          role: "user", 
          parts, 
          timestamp: new Date().toISOString() 
        }),
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`Error saving message: ${errorText}`);
      }
      
      reloadHistory();
    } catch (error) {
      console.error("Error saving user message:", error);
    }
  };


  const searchParams = useSearchParams();
  const query = searchParams.get("query");
  const [hasAppendedQuery, setHasAppendedQuery] = useState(false);
  useEffect(() => {
    if (query && !hasAppendedQuery) {
      handleSend([{ type: "text", text: query }]);
      setHasAppendedQuery(true);
      window.history.replaceState({}, "", `/`);
    }
  }, [query, hasAppendedQuery]);

  const { data: votes } = useSWR<Vote[]>(
    messages.length >= 2 ? `/api/vote?chatId=${id}` : null,
    fetcher
  );

  const [attachments, setAttachments] = useState([]);
  const isArtifactVisible = useArtifactSelector((state) => state.isVisible);
  useAutoResume({ autoResume, initialMessages, resumeStream, setMessages });

  if (historyError) {
    return <div className="p-8 text-center">Failed to load chat history.</div>;
  }
  return (
    <>
      <div className="flex flex-col min-w-0 h-dvh bg-white dark:bg-black">
        <div className="border-b border-gray-200 dark:border-gray-800 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                <svg
                  className="w-4 h-4 text-white"
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
                className="w-5 h-5 text-gray-600 dark:text-gray-300"
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

        <div className="flex-1 overflow-auto relative">
          {messages.length === 0 && (
            <div className="absolute inset-0 flex flex-col items-center justify-center p-8">
              <div className="text-center max-w-md">
                <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center mb-4 mx-auto">
                  <svg
                    className="w-6 h-6 text-white"
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
                      const message = "Create a task to buy groceries";
                      sendMessage({
                        role: "user" as const,
                        parts: [{ type: "text", text: message }],
                      });
                    }}
                    className="w-full border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:bg-gray-50 dark:hover:bg-gray-900/50 transition-colors text-left"
                  >
                    <span className="text-gray-700 dark:text-gray-300 text-sm">
                      "Create a task to buy groceries"
                    </span>
                  </button>
                  <button
                    onClick={() => {
                      const message = "Show me all my tasks";
                      sendMessage({
                        role: "user" as const,
                        parts: [{ type: "text", text: message }],
                      });
                    }}
                    className="w-full border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:bg-gray-50 dark:hover:bg-gray-900/50 transition-colors text-left"
                  >
                    <span className="text-gray-700 dark:text-gray-300 text-sm">
                      "Show me all my tasks"
                    </span>
                  </button>
                </div>
              </div>
            </div>
          )}

        <Messages
          chatId={id}
          status={status}
          votes={votes}
          messages={messages}
          setMessages={setMessages}
          regenerate={regenerate}
          isReadonly={isReadonly}
          isArtifactVisible={isArtifactVisible}
        />
        </div>

        <div className="border-t border-gray-200 dark:border-gray-800 p-3">
          <form className="max-w-4xl mx-auto">
          {!isReadonly && (
            <MultimodalInput
              chatId={id}
              input={input}
              setInput={setInput}
              status={status}
              stop={stop}
              attachments={attachments}
              setAttachments={setAttachments}
              messages={messages}
              setMessages={setMessages}
              sendMessage={sendMessage}
              selectedVisibilityType={visibilityType}
            />
          )}
        </form>
        </div>
      </div>

      <Artifact
        chatId={id}
        input={input}
        setInput={setInput}
        status={status}
        stop={stop}
        attachments={attachments}
        setAttachments={setAttachments}
        sendMessage={sendMessage}
        messages={messages}
        setMessages={setMessages}
        regenerate={regenerate}
        votes={votes}
        isReadonly={isReadonly}
        selectedVisibilityType={visibilityType}
      />
    </>
  );
}

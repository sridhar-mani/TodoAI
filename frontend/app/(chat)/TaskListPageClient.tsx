"use client";
import { useState } from "react";
import { Chat } from "@/components/chat";
import { TaskList } from "@/components/task-list";
import { DataStreamHandler } from "@/components/data-stream-handler";

export default function TaskListPageClient({
  id,
  chatModel,
}: {
  id: string;
  chatModel: string;
}) {
  const [collapsed, setCollapsed] = useState(false);
  return (
    <div className="flex h-screen bg-white dark:bg-black">
      <div
        className={`${
          collapsed ? "w-full" : "w-2/3"
        } h-full transition-all duration-300 ease-in-out`}
      >
        <Chat
          key={id}
          id={id}
          initialMessages={[]}
          initialChatModel={chatModel}
          initialVisibilityType="private"
          isReadonly={false}
          autoResume={false}
        />
        <DataStreamHandler />
      </div>

      <div
        className={`${
          collapsed ? "w-0 overflow-hidden" : "w-1/3"
        } h-full border-l border-gray-200 dark:border-gray-800 transition-all duration-300 ease-in-out`}
      >
        <button
          className="absolute top-6 right-6 z-20 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-full p-3 shadow-md hover:shadow-lg transition-all duration-200 border border-gray-200 dark:border-gray-700"
          onClick={() => setCollapsed((prev) => !prev)}
          aria-label={collapsed ? "Expand task list" : "Collapse task list"}
        >
          {collapsed ? (
            <svg
              width="20"
              height="20"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="text-gray-600 dark:text-gray-300"
            >
              <polyline points="15 18 9 12 15 6" />
            </svg>
          ) : (
            <svg
              width="20"
              height="20"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="text-gray-600 dark:text-gray-300"
            >
              <polyline points="9 18 15 12 9 6" />
            </svg>
          )}
        </button>

        <div className="h-full">
          {!collapsed && <TaskList />}
          {collapsed && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center p-4">
                <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center mb-3 mx-auto">
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
                      d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                    />
                  </svg>
                </div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-300 mb-1">
                  Tasks
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Click to expand
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

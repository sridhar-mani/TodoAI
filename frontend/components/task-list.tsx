"use client";

import { useEffect, useState } from "react";
import useSWR, { useSWRConfig } from "swr";
import { fetcher } from "@/lib/utils";
import { Task } from "@/lib/types";
import { useSocket } from "@/hooks/use-socket";

interface TaskListResponse {
  tasks: Task[];
  total: number;
  skip: number;
  limit: number;
}

const StatusIcon = ({
  status,
  onClick,
}: {
  status: string;
  onClick?: () => void;
}) => {
  const className = `w-5 h-5 rounded-full cursor-pointer hover:scale-110 transition-transform ${
    onClick ? "hover:opacity-80" : ""
  }`;

  switch (status) {
    case "completed":
      return (
        <div
          className={`${className} bg-gray-400 dark:bg-gray-500 flex items-center justify-center`}
          onClick={onClick}
        >
          <svg
            className="w-3 h-3 text-white"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
              clipRule="evenodd"
            />
          </svg>
        </div>
      );
    case "in_progress":
      return (
        <div
          className={`${className} bg-blue-500 animate-pulse`}
          onClick={onClick}
        ></div>
      );
    default:
      return (
        <div
          className={`${className} border-2 border-gray-300 dark:border-gray-600`}
          onClick={onClick}
        ></div>
      );
  }
};

const PriorityDot = ({ priority }: { priority: string }) => {
  const getIntensity = () => {
    switch (priority) {
      case "urgent":
        return "bg-red-600";
      case "high":
        return "bg-red-500";
      case "medium":
        return "bg-yellow-400";
      case "low":
        return "bg-green-400";
      default:
        return "bg-gray-400";
    }
  };

  return <div className={`w-2 h-2 rounded-full ${getIntensity()}`}></div>;
};

const TaskEditModal = ({
  task,
  isOpen,
  onClose,
  onSave,
}: {
  task: Task | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (updatedTask: Partial<Task>) => void;
}) => {
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    status: "pending",
    priority: "medium",
    due_date: "",
  });

  useEffect(() => {
    if (task) {
      setFormData({
        title: task.title || "",
        description: task.description || "",
        status: task.status || "pending",
        priority: task.priority || "medium",
        due_date: task.due_date
          ? new Date(task.due_date).toISOString().split("T")[0]
          : "",
      });
    }
  }, [task]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (task) {
      onSave({
        id: task.id,
        ...formData,
        due_date: formData.due_date
          ? new Date(formData.due_date).toISOString()
          : null,
      });
    }
  };

  if (!isOpen || !task) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md mx-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-black dark:text-white">
            Edit Task
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Title
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) =>
                setFormData({ ...formData, title: e.target.value })
              }
              className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-black dark:text-white"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
              className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-black dark:text-white"
              rows={3}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Status
              </label>
              <select
                value={formData.status}
                onChange={(e) =>
                  setFormData({ ...formData, status: e.target.value })
                }
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-black dark:text-white"
              >
                <option value="pending">Pending</option>
                <option value="in_progress">In Progress</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Priority
              </label>
              <select
                value={formData.priority}
                onChange={(e) =>
                  setFormData({ ...formData, priority: e.target.value })
                }
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-black dark:text-white"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Due Date
            </label>
            <input
              type="date"
              value={formData.due_date}
              onChange={(e) =>
                setFormData({ ...formData, due_date: e.target.value })
              }
              className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-black dark:text-white"
            />
          </div>

          <div className="flex space-x-3 pt-4">
            <button
              type="submit"
              className="flex-1 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md transition-colors"
            >
              Save Changes
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-300 hover:bg-gray-400 dark:bg-gray-600 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-200 px-4 py-2 rounded-md transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export function TaskList() {
  const { data, error, mutate } = useSWR<TaskListResponse>(
    "/api/tasks?skip=0&limit=100",
    fetcher
  );
  const socket = useSocket();
  const { mutate: globalMutate } = useSWRConfig();
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterDate, setFilterDate] = useState("");
  const [showNewTaskForm, setShowNewTaskForm] = useState(false);
  const [isUpdating, setIsUpdating] = useState<number | null>(null);
  const [newTask, setNewTask] = useState({
    title: "",
    description: "",
    priority: "medium",
    due_date: "",
  });

  const handleApiCall = async (
    apiCall: () => Promise<Response>,
    successMessage?: string,
    taskId?: number
  ) => {
    try {
      setIsUpdating(taskId || null);
      const response = await apiCall();
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
      }

      await mutate();
     
      return response;
    } catch (error) {
      console.error("API call failed:", error);
      alert(`Operation failed: ${error.message}`);
      throw error;
    } finally {
      setIsUpdating(null);
    }
  };

  const handleStatusToggle = async (task: Task) => {
    const statusOrder = ["pending", "in_progress", "completed"];
    const currentIndex = statusOrder.indexOf(task.status);
    const nextStatus = statusOrder[(currentIndex + 1) % statusOrder.length];

    await handleApiCall(
      () => fetch(`/api/tasks`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_id: task.id,
          status: nextStatus,
        }),
      }),
      `Task ${task.id} status updated to ${nextStatus}`,
      task.id
    );
  };

  const handleQuickAction = async (task: Task, action: string) => {
    await handleApiCall(
      () => fetch(`/api/tasks`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_id: task.id,
          status: action,
        }),
      }),
      `Task ${task.id} updated to ${action}`,
      task.id
    );
  };

  const handleDeleteTask = async (taskId: number) => {
    if (!confirm("Delete this task?")) return;

    await handleApiCall(
      () => fetch(`/api/tasks/delete/${taskId}`, {
        method: "DELETE",
      }),
      `Task ${taskId} deleted`,
      taskId
    );
  };

  const handleCreateTask = async () => {
    if (!newTask.title.trim()) {
      alert("Task title is required");
      return;
    }

    await handleApiCall(
      () => fetch(`/api/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...newTask,
          due_date: newTask.due_date
            ? new Date(newTask.due_date).toISOString()
            : null,
        }),
      }),
      "Task created successfully"
    );

    setNewTask({
      title: "",
      description: "",
      priority: "medium",
      due_date: "",
    });
    setShowNewTaskForm(false);
  };

  const handleSaveTask = async (updatedTask: Partial<Task>) => {
    const { id, ...taskData } = updatedTask;
    
    await handleApiCall(
      () => fetch(`/api/tasks`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_id: id,
          ...taskData,
        }),
      }),
      `Task ${id} updated successfully`,
      id as number
    );

    setIsModalOpen(false);
    setEditingTask(null);
  };

  useEffect(() => {
    if (socket) {
      const handleTaskUpdate = () => {
        mutate();
      };

      socket.on("task_list_update", handleTaskUpdate);
      
      return () => {
        socket.off("task_list_update");
      };
    }
  }, [socket, mutate]);

  if (!data && !error) {
    return (
      <div className="flex items-center justify-center h-full p-8">
        <div className="text-center">
          <div className="w-12 h-12 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center mb-4 mx-auto animate-pulse">
            <div className="w-6 h-6 rounded-full bg-blue-500"></div>
          </div>
          <p className="text-gray-600 dark:text-gray-400">Loading tasks...</p>
        </div>
      </div>
    );
  }
  if (error) {
    return (
      <div className="flex items-center justify-center h-full p-8">
        <div className="text-center">
          <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mb-4 mx-auto">
            <svg
              className="w-6 h-6 text-red-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.464 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z"
              />
            </svg>
          </div>
          <p className="text-red-600 dark:text-red-400 mb-2">Failed to load tasks</p>
          <button
            onClick={() => mutate()}
            className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white text-sm rounded-md transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const filteredTasks = data.tasks.filter((task) => {
    const matchesSearch =
      searchTerm === "" ||
      task.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (task.description &&
        task.description.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesDate =
      filterDate === "" ||
      (task.due_date &&
        new Date(task.due_date).toDateString() ===
          new Date(filterDate).toDateString());

    return matchesSearch && matchesDate;
  });

  const completedTasks = filteredTasks.filter((task) => task.status === "completed").length;
  const pendingTasks = filteredTasks.filter((task) => task.status === "pending").length;
  const inProgressTasks = filteredTasks.filter((task) => task.status === "in_progress").length;

  return (
    <div className="h-full bg-white dark:bg-black flex flex-col">

      <div className="border-b border-gray-200 dark:border-gray-800 p-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-lg font-semibold text-black dark:text-white">
              Tasks
            </h1>
            <p className="text-gray-500 dark:text-gray-400 text-xs">
              {data.total} items
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowNewTaskForm(!showNewTaskForm)}
              className="px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white text-sm rounded-md transition-colors"
            >
              Add Task
            </button>
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-xs text-gray-500 dark:text-gray-400">
                Live
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-8 mb-4">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full border-2 border-blue-500"></div>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {pendingTasks} Pending
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-blue-500"></div>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {inProgressTasks} Active
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-gray-400"></div>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {completedTasks} Done
            </span>
          </div>
        </div>

        <div className="flex space-x-4">
          <input
            type="text"
            placeholder="Search tasks..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-black dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
          />
          <input
            type="date"
            value={filterDate}
            onChange={(e) => setFilterDate(e.target.value)}
            className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-black dark:text-white"
          />
          {(searchTerm || filterDate) && (
            <button
              onClick={() => {
                setSearchTerm("");
                setFilterDate("");
              }}
              className="px-3 py-2 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              Clear
            </button>
          )}
        </div>

        {showNewTaskForm && (
          <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className="space-y-3">
              <input
                type="text"
                placeholder="Task title"
                value={newTask.title}
                onChange={(e) =>
                  setNewTask({ ...newTask, title: e.target.value })
                }
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-black dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
              />
              <textarea
                placeholder="Description (optional)"
                value={newTask.description}
                onChange={(e) =>
                  setNewTask({ ...newTask, description: e.target.value })
                }
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-black dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
                rows={2}
              />
              <div className="flex space-x-3">
                <select
                  value={newTask.priority}
                  onChange={(e) =>
                    setNewTask({ ...newTask, priority: e.target.value })
                  }
                  className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-black dark:text-white"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
                <input
                  type="date"
                  value={newTask.due_date}
                  onChange={(e) =>
                    setNewTask({ ...newTask, due_date: e.target.value })
                  }
                  className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-black dark:text-white"
                />
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={handleCreateTask}
                  disabled={isUpdating !== null}
                  className="px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-blue-300 text-white text-sm rounded-md transition-colors"
                >
                  {isUpdating !== null ? "Creating..." : "Create Task"}
                </button>
                <button
                  onClick={() => {
                    setShowNewTaskForm(false);
                    setNewTask({
                      title: "",
                      description: "",
                      priority: "medium",
                      due_date: "",
                    });
                  }}
                  className="px-4 py-2 bg-gray-300 hover:bg-gray-400 dark:bg-gray-600 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-200 text-sm rounded-md transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto">
        {filteredTasks.length === 0 ? (
          <div className="flex items-center justify-center h-full p-8">
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-4 mx-auto">
                <svg
                  className="w-8 h-8 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                No tasks found
              </h3>
              <p className="text-gray-500 dark:text-gray-400 mb-4">
                {searchTerm || filterDate ? "Try adjusting your filters" : "Create your first task to get started"}
              </p>
              {!searchTerm && !filterDate && (
                <div className="inline-flex items-center px-3 py-1 rounded-full bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 text-sm">
                  Say: "Create a task to buy groceries"
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="p-4 space-y-2">
            {filteredTasks.map((task) => (
              <div
                key={task.id}
                className={`group flex items-center space-x-4 p-4 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-900/50 transition-colors border border-transparent hover:border-gray-200 dark:hover:border-gray-800 ${
                  isUpdating === task.id ? "opacity-50 pointer-events-none" : ""
                }`}
              >
                <StatusIcon
                  status={task.status}
                  onClick={() => handleStatusToggle(task)}
                />

                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <h3
                      className={`font-medium text-black dark:text-white truncate ${
                        task.status === "completed"
                          ? "line-through opacity-60"
                          : ""
                      }`}
                    >
                      {task.title}
                    </h3>
                    <PriorityDot priority={task.priority} />
                  </div>

                  {task.description && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                      {task.description}
                    </p>
                  )}

                  <div className="flex items-center justify-between mt-2">
                    <div className="flex items-center space-x-4">
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        #{task.id}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                        {task.priority}
                      </span>
                    </div>

                    <div className="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
                      {task.due_date && (
                        <div className="flex items-center space-x-1">
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                          <span>
                            Due {new Date(task.due_date).toLocaleDateString("en-US", {
                              month: "short",
                              day: "numeric",
                              year: new Date(task.due_date).getFullYear() !== new Date().getFullYear() ? "numeric" : undefined,
                            })}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <div className="opacity-0 group-hover:opacity-100 transition-opacity flex space-x-1">
                  {task.status !== "in_progress" && (
                    <button
                      onClick={() => handleQuickAction(task, "in_progress")}
                      disabled={isUpdating === task.id}
                      className="p-1 rounded hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors disabled:opacity-50"
                      title="Mark as active"
                    >
                      <svg className="w-4 h-4 text-blue-500 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1M5 12l10 7" />
                      </svg>
                    </button>
                  )}
                  {task.status !== "completed" && (
                    <button
                      onClick={() => handleQuickAction(task, "completed")}
                      disabled={isUpdating === task.id}
                      className="p-1 rounded hover:bg-green-200 dark:hover:bg-green-900/50 transition-colors disabled:opacity-50"
                      title="Mark as done"
                    >
                      <svg className="w-4 h-4 text-green-500 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </button>
                  )}
                  <button
                    onClick={() => {
                      setEditingTask(task);
                      setIsModalOpen(true);
                    }}
                    disabled={isUpdating === task.id}
                    className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
                    title="Edit task"
                  >
                    <svg className="w-4 h-4 text-gray-500 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => handleDeleteTask(task.id)}
                    disabled={isUpdating === task.id}
                    className="p-1 rounded hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors disabled:opacity-50"
                    title="Delete task"
                  >
                    <svg className="w-4 h-4 text-red-500 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>

                {isUpdating === task.id && (
                  <div className="absolute inset-0 flex items-center justify-center bg-white/50 dark:bg-black/50 rounded-lg">
                    <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <TaskEditModal
        task={editingTask}
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingTask(null);
        }}
        onSave={handleSaveTask}
      />
    </div>
  );
}
"use client";

import { useEffect, useState } from "react";
import useSWR, { useSWRConfig } from "swr";
import { fetcher } from "@/lib/utils";
import { Task } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useSocket } from "@/hooks/use-socket";
import {
  CheckCircle,
  Circle,
  Clock,
  AlertTriangle,
  Edit,
  Trash2,
  Plus,
} from "lucide-react";

interface TaskListResponse {
  tasks: Task[];
  total: number;
  skip: number;
  limit: number;
}

interface EnhancedTaskListProps {
  searchTerm?: string;
  filterStatus?: string;
  filterPriority?: string;
}

export function EnhancedTaskList({
  searchTerm = "",
  filterStatus = "all",
  filterPriority = "all",
}: EnhancedTaskListProps) {
  const { data, error, mutate } = useSWR<TaskListResponse>(
    "/api/tasks?skip=0&limit=100",
    fetcher
  );
  const socket = useSocket();
  const { mutate: globalMutate } = useSWRConfig();
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);

  useEffect(() => {
    if (socket) {
      socket.on("task_list_update", () => {
        mutate();
        globalMutate("/api/tasks?skip=0&limit=100");
      });
    }

    return () => {
      if (socket) {
        socket.off("task_list_update");
      }
    };
  }, [socket, mutate, globalMutate]);

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case "high":
        return "bg-red-100 text-red-800 border-red-200";
      case "medium":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "low":
        return "bg-green-100 text-green-800 border-green-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case "completed":
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case "in_progress":
        return <Clock className="w-5 h-5 text-blue-600" />;
      case "pending":
        return <Circle className="w-5 h-5 text-gray-400" />;
      default:
        return <Circle className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "completed":
        return "bg-green-100 text-green-800 border-green-200";
      case "in_progress":
        return "bg-blue-100 text-blue-800 border-blue-200";
      case "pending":
        return "bg-gray-100 text-gray-800 border-gray-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const isOverdue = (dueDate: string) => {
    return (
      new Date(dueDate) < new Date() &&
      new Date(dueDate).toDateString() !== new Date().toDateString()
    );
  };

  const filteredTasks =
    data?.tasks.filter((task) => {
      const matchesSearch =
        task.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        task.description?.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus =
        filterStatus === "all" ||
        task.status.toLowerCase() === filterStatus.toLowerCase();
      const matchesPriority =
        filterPriority === "all" ||
        task.priority.toLowerCase() === filterPriority.toLowerCase();

      return matchesSearch && matchesStatus && matchesPriority;
    }) || [];

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-red-600">
            <AlertTriangle className="w-12 h-12 mx-auto mb-4" />
            <p>Failed to load tasks</p>
            <Button onClick={() => mutate()} className="mt-2">
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p>Loading tasks...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Tasks</p>
                <p className="text-2xl font-bold">{data.total}</p>
              </div>
              <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                <Plus className="w-5 h-5 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Pending</p>
                <p className="text-2xl font-bold text-yellow-600">
                  {data.tasks.filter((t) => t.status === "pending").length}
                </p>
              </div>
              <div className="w-10 h-10 bg-yellow-100 rounded-full flex items-center justify-center">
                <Circle className="w-5 h-5 text-yellow-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">In Progress</p>
                <p className="text-2xl font-bold text-blue-600">
                  {data.tasks.filter((t) => t.status === "in_progress").length}
                </p>
              </div>
              <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                <Clock className="w-5 h-5 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Completed</p>
                <p className="text-2xl font-bold text-green-600">
                  {data.tasks.filter((t) => t.status === "completed").length}
                </p>
              </div>
              <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                <CheckCircle className="w-5 h-5 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Task List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Tasks ({filteredTasks.length})</span>
            <Button size="sm" className="flex items-center gap-2">
              <Plus className="w-4 h-4" />
              Add Task
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {filteredTasks.length === 0 ? (
            <div className="text-center py-8">
              <Circle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No tasks found</p>
              <p className="text-sm text-gray-500">
                Try adjusting your filters or create a new task
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredTasks.map((task) => (
                <div
                  key={task.id}
                  className={`p-4 border rounded-lg hover:shadow-md transition-shadow cursor-pointer ${
                    selectedTask?.id === task.id ? "ring-2 ring-blue-500" : ""
                  } ${
                    isOverdue(task.due_date) ? "border-red-200 bg-red-50" : ""
                  }`}
                  onClick={() => setSelectedTask(task)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        {getStatusIcon(task.status)}
                        <h3 className="font-semibold text-lg">{task.title}</h3>
                        {isOverdue(task.due_date) && (
                          <Badge variant="destructive" className="text-xs">
                            Overdue
                          </Badge>
                        )}
                      </div>

                      {task.description && (
                        <p className="text-gray-600 mb-3 line-clamp-2">
                          {task.description}
                        </p>
                      )}

                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        <div className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          <span>
                            Due: {new Date(task.due_date).toLocaleDateString()}
                          </span>
                        </div>

                        <Badge
                          className={`text-xs ${getPriorityColor(
                            task.priority
                          )}`}
                        >
                          {task.priority}
                        </Badge>

                        <Badge
                          className={`text-xs ${getStatusColor(task.status)}`}
                        >
                          {task.status.replace("_", " ")}
                        </Badge>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 ml-4">
                      <Button size="sm" variant="outline" className="p-1">
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="p-1 text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

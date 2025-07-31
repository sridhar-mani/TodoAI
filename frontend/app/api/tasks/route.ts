import { NextResponse } from "next/server";

const BACKEND_URL =
  process.env.BACKEND_URL || "http://localhost:8000/api/tasks";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const skip = searchParams.get("skip") || "0";
  const limit = searchParams.get("limit") || "100";
  try {
    const res = await fetch(`${BACKEND_URL}?skip=${skip}&limit=${limit}`);
    if (!res.ok) throw new Error("Backend error");
    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    // Fallback static task list for testing
    const fallbackTasks = [
      {
        id: 1,
        title: "Test Task 1",
        description: "This is a fallback test task",
        status: "pending",
        due_date: new Date().toISOString(),
        priority: "high",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: 2,
        title: "Test Task 2",
        description: "Another fallback task",
        status: "in_progress",
        due_date: new Date().toISOString(),
        priority: "medium",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: 3,
        title: "Test Task 3",
        description: "Yet another fallback task",
        status: "completed",
        due_date: new Date().toISOString(),
        priority: "low",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ];
    return NextResponse.json({
      tasks: fallbackTasks,
      total: fallbackTasks.length,
      skip: Number(skip),
      limit: Number(limit),
      fallback: true,
    });
  }
}

export async function POST(request: Request) {
  const body = await request.json();
  const res = await fetch(`${BACKEND_URL}/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  return NextResponse.json(data);
}

export async function PUT(request: Request) {
  try {
    const body = await request.json();
    const { task_id, ...updateData } = body;

    if (!task_id) {
      return NextResponse.json(
        { error: "task_id is required" },
        { status: 400 }
      );
    }


    const res = await fetch(`${BACKEND_URL}/update/${task_id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updateData),
    });

    if (!res.ok) {
      const errorText = await res.text();
      return NextResponse.json(
        { error: "Failed to update task", details: errorText },
        { status: res.status }
      );
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
export async function DELETE(request: Request) {
  const { task_id } = await request.json();
  const res = await fetch(`${BACKEND_URL}/delete/${task_id}`, {
    method: "DELETE",
  });
  const data = await res.json();
  return NextResponse.json(data);
}

export async function GET_BY_ID(request: Request) {
  const { searchParams } = new URL(request.url);
  const task_id = searchParams.get("task_id");
  if (!task_id)
    return NextResponse.json({ error: "task_id required" }, { status: 400 });
  const res = await fetch(`${BACKEND_URL}/get/${task_id}`);
  const data = await res.json();
  return NextResponse.json(data);
}

export async function GET_FILTER(request: Request) {
  const { searchParams } = new URL(request.url);
  const status = searchParams.get("status");
  const priority = searchParams.get("priority");
  const due_before = searchParams.get("due_before");
  const dur_after = searchParams.get("dur_after");
  const params = new URLSearchParams();
  if (status) params.append("status", status);
  if (priority) params.append("priority", priority);
  if (due_before) params.append("due_before", due_before);
  if (dur_after) params.append("dur_after", dur_after);
  const res = await fetch(
    `${BACKEND_URL}/filter-by-criteria?${params.toString()}`
  );
  const data = await res.json();
  return NextResponse.json(data);
}

export async function GET_SEARCH(request: Request) {
  const { searchParams } = new URL(request.url);
  const search_term = searchParams.get("search_term") || "";
  const skip = searchParams.get("skip") || "0";
  const limit = searchParams.get("limit") || "100";
  const res = await fetch(
    `${BACKEND_URL}/search/?search_term=${encodeURIComponent(
      search_term
    )}&skip=${skip}&limit=${limit}`
  );
  const data = await res.json();
  return NextResponse.json(data);
}

export async function GET_OVERDUE(request: Request) {
  const res = await fetch(`${BACKEND_URL}/get-overdue-tasks`);
  const data = await res.json();
  return NextResponse.json(data);
}

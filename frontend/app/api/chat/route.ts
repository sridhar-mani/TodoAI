import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";
const BACKEND_CHAT_URL = `${BACKEND_URL}/api/tasks/chat`;

export async function POST(request: NextRequest) {
  try {
    const { messages, id, selectedChatModel } = await request.json();

    const lastMessage = messages[messages.length - 1];

    if (!lastMessage || lastMessage.role !== "user") {
      return NextResponse.json(
        { error: "Invalid message format" },
        { status: 400 }
      );
    }

    let messageContent = "";
    if (lastMessage.content) {
      messageContent = lastMessage.content;
    } else if (lastMessage.parts && lastMessage.parts.length > 0) {
      messageContent = lastMessage.parts
        .filter((part: any) => part.type === "text")
        .map((part: any) => part.text)
        .join(" ");
    } else {
      return NextResponse.json(
        { error: "No message content found" },
        { status: 400 }
      );
    }


    try {

      const response = await fetch(BACKEND_CHAT_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: messageContent,
          chat_id: id,
          model: selectedChatModel,
          user_id: id,
        }),
      });


      if (response.ok) {
        const data = await response.json();

        const encoder = new TextEncoder();
        const stream = new ReadableStream({
          start(controller) {
            const responseText =
              data.message || data.response || "Task completed.";

            const chunk = {
              id: data.id || `msg_${Date.now()}`,
              role: "assistant",
              content: responseText,
            };

            controller.enqueue(
              encoder.encode(`data: ${JSON.stringify(chunk)}\n\n`)
            );
            controller.close();
          },
        });

        return new Response(stream, {
          headers: {
            "Content-Type": "text/plain; charset=utf-8",
            "Transfer-Encoding": "chunked",
          },
        });
      } else {
        const errorText = await response.text();
      }
    } catch (backendError) {
      console.warn("Backend connection failed:", backendError);
    }

    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        const chunk = {
          id: `msg_${Date.now()}`,
          role: "assistant",
          content:
            "I'm a task management assistant. Please make sure the backend server is running to use the full task management features.",
        };

        controller.enqueue(
          encoder.encode(`data: ${JSON.stringify(chunk)}\n\n`)
        );
        controller.close();
      },
    });

    return new Response(stream, {
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Transfer-Encoding": "chunked",
      },
    });
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to process chat message" },
      { status: 500 }
    );
  }
}

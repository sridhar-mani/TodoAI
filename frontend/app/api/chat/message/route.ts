import { NextRequest, NextResponse } from 'next/server';

const FASTAPI_URL = process.env.NEXT_PUBLIC_SOCKET_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    const messageData = await request.json();
    
    // Forward the message to the FastAPI backend
    const response = await fetch(`${FASTAPI_URL}/api/chat/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(messageData),
    });

    if (!response.ok) {
      const errorText = await response.text();
      return NextResponse.json(
        { error: `Failed to save message: ${response.statusText}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to save message' },
      { status: 500 }
    );
  }
}

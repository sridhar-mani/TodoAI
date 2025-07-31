import { NextRequest, NextResponse } from 'next/server';

const FASTAPI_URL = process.env.NEXT_PUBLIC_SOCKET_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  try {
    
    const response = await fetch(`${FASTAPI_URL}/api/chat/history`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      return NextResponse.json(
        { error: `FastAPI error: ${response.statusText}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to fetch chat history' },
      { status: 500 }
    );
  }
}

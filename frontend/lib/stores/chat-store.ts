import { createContext, useContext, useReducer, ReactNode } from 'react';
import type { ChatMessage } from '@/lib/types';

interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
}

type ChatAction = 
  | { type: 'ADD_MESSAGE'; payload: ChatMessage }
  | { type: 'UPDATE_MESSAGE'; payload: { id: string; content: string } }
  | { type: 'CLEAR_MESSAGES' }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'LOAD_MESSAGES'; payload: ChatMessage[] };

interface ChatContextType {
  state: ChatState;
  addMessage: (message: ChatMessage) => void;
  updateMessage: (id: string, content: string) => void;
  clearMessages: () => void;
  setLoading: (loading: boolean) => void;
  loadMessages: (messages: ChatMessage[]) => void;
}

const initialState: ChatState = {
  messages: [],
  isLoading: false,
};

function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'ADD_MESSAGE':
      return {
        ...state,
        messages: [...state.messages, action.payload]
      };
    case 'UPDATE_MESSAGE':
      return {
        ...state,
        messages: state.messages.map(msg => 
          msg.id === action.payload.id 
            ? { ...msg, parts: [{ type: 'text', text: action.payload.content }] }
            : msg
        )
      };
    case 'CLEAR_MESSAGES':
      return {
        ...state,
        messages: []
      };
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload
      };
    case 'LOAD_MESSAGES':
      return {
        ...state,
        messages: action.payload
      };
    default:
      return state;
  }
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(chatReducer, initialState);

  const addMessage = (message: ChatMessage) => {
    dispatch({ type: 'ADD_MESSAGE', payload: message });
    // Save to localStorage
    const updatedMessages = [...state.messages, message];
    localStorage.setItem('chat-messages', JSON.stringify(updatedMessages));
  };

  const updateMessage = (id: string, content: string) => {
    dispatch({ type: 'UPDATE_MESSAGE', payload: { id, content } });
    // Save to localStorage
    const updatedMessages = state.messages.map(msg => 
      msg.id === id 
        ? { ...msg, parts: [{ type: 'text', text: content }] }
        : msg
    );
    localStorage.setItem('chat-messages', JSON.stringify(updatedMessages));
  };

  const clearMessages = () => {
    dispatch({ type: 'CLEAR_MESSAGES' });
    localStorage.removeItem('chat-messages');
  };

  const setLoading = (loading: boolean) => {
    dispatch({ type: 'SET_LOADING', payload: loading });
  };

  const loadMessages = (messages: ChatMessage[]) => {
    dispatch({ type: 'LOAD_MESSAGES', payload: messages });
  };

  return (
    <ChatContext.Provider value={{
      state,
      addMessage,
      updateMessage,
      clearMessages,
      setLoading,
      loadMessages
    }}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChatStore() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChatStore must be used within a ChatProvider');
  }
  return context;
}

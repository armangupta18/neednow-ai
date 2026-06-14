"use client";

import { ChatWindow } from "@/components/chat";

export default function ChatPage() {
  return (
    <div className="mx-auto flex h-[calc(100vh-64px)] max-w-4xl flex-col">
      <ChatWindow />
    </div>
  );
}

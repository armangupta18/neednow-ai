"use client";

import { useRef, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useChat } from "@/hooks/useChat";
import { useCart } from "@/hooks/useCart";
import { useSpeechSynthesis } from "@/hooks/useSpeechSynthesis";
import MessageBubble from "./MessageBubble";
import ProductCards from "./ProductCards";
import TypingIndicator from "./TypingIndicator";
import Suggestions from "./Suggestions";
import ChatInput from "./ChatInput";
import { CHAT_WELCOME_MESSAGE } from "@/constants/prompts";
import { ROUTES } from "@/constants/routes";
import { cn } from "@/lib/utils";

export default function ChatWindow() {
  const router = useRouter();
  const {
    messages,
    lastResult,
    isTyping,
    sendMessage,
    clearChat,
  } = useChat();

  const { addItem, itemCount } = useCart();
  const [showCartBar, setShowCartBar] = useState(false);

  const { isMuted, isSpeaking, speak, stop, toggleMute, isSupported: ttsSupported } =
    useSpeechSynthesis();

  const scrollRef = useRef<HTMLDivElement>(null);
  const prevMessageCount = useRef(messages.length);

  // Auto-scroll on new messages
  useEffect(() => {
    const el = scrollRef.current;
    if (el) {
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    }
  }, [messages, isTyping]);

  // Handle navigation actions from assistant messages
  useEffect(() => {
    if (messages.length > prevMessageCount.current) {
      const lastMsg = messages[messages.length - 1];
      if (lastMsg?.role === "assistant" && lastMsg.metadata) {
        const nav = lastMsg.metadata.navigate as string | undefined;
        if (nav) {
          setTimeout(() => router.push(nav), 800);
        }
        // Show cart bar after add-to-cart actions
        const action = lastMsg.metadata.action as string | undefined;
        if (action === "added_to_cart" || action === "added_all_to_cart" || action === "buy_now") {
          setShowCartBar(true);
        }
      }
      // Read aloud (skip JSON and navigation messages)
      if (lastMsg?.role === "assistant" && !lastMsg.metadata?.error) {
        const content = lastMsg.content;
        if (content && !content.startsWith("{") && !content.startsWith("[")) {
          speak(content);
        }
      }
    }
    prevMessageCount.current = messages.length;
  }, [messages, speak, router]);

  const handleSuggestion = (text: string) => {
    sendMessage(text);
  };

  const handleAddToCart = (productId: string) => {
    const product = lastResult?.cart?.products?.find((p: { id: string }) => p.id === productId);
    if (product) {
      addItem(productId);
      setShowCartBar(true);
    }
  };

  const handleBuyNow = () => {
    if (lastResult?.cart?.products?.[0]) {
      addItem(lastResult.cart.products[0].id);
    }
    router.push(ROUTES.CHECKOUT);
  };

  // Show product cards only after the last assistant message with products
  const shouldShowProducts = (msgIndex: number) => {
    return (
      msgIndex === messages.length - 1 &&
      messages[msgIndex]?.role === "assistant" &&
      !messages[msgIndex]?.metadata?.action && // Don't show after action confirmations
      !isTyping &&
      lastResult?.cart?.products &&
      lastResult.cart.products.length > 0
    );
  };

  const isEmpty = messages.length === 0;

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-sm">🤖</span>
          <div>
            <h2 className="text-sm font-semibold text-slate-800">NeedNow AI</h2>
            <p className="text-[10px] text-slate-400">
              {isTyping ? "Finding products..." : isSpeaking ? "Speaking..." : "Ready to help"}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {ttsSupported && (
            <button
              onClick={() => { if (isSpeaking) stop(); toggleMute(); }}
              className={cn(
                "flex h-8 w-8 items-center justify-center rounded-lg transition",
                isMuted ? "text-slate-400 hover:bg-slate-100" : "text-blue-600 hover:bg-blue-50"
              )}
              aria-label={isMuted ? "Unmute" : "Mute"}
            >
              {isMuted ? "🔇" : "🔊"}
            </button>
          )}
          {messages.length > 0 && (
            <button onClick={clearChat} className="rounded-md px-2 py-1 text-xs text-slate-500 hover:bg-slate-100">
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {isEmpty && (
          <div className="flex flex-col items-center justify-center h-full text-center gap-6 py-12">
            <div>
              <span className="text-4xl">🛒</span>
              <h3 className="mt-3 text-lg font-semibold text-slate-700">Welcome to NeedNow AI</h3>
              <p className="mt-1 max-w-sm text-sm text-slate-500">{CHAT_WELCOME_MESSAGE}</p>
              <p className="mt-2 text-xs text-slate-400">
                🎙️ Try: &quot;Order eco shampoo&quot; • &quot;Find bandages&quot; • &quot;I need toothpaste&quot;
              </p>
            </div>
            <Suggestions onSelect={handleSuggestion} />
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={msg.id}>
            <MessageBubble
              role={msg.role}
              content={msg.content}
              timestamp={msg.timestamp}
              isError={!!msg.metadata?.error}
            />
            {shouldShowProducts(idx) && lastResult?.cart?.products && (
              <div className="ml-0 mt-2 max-w-[85%]">
                <ProductCards
                  products={lastResult.cart.products}
                  onAddToCart={handleAddToCart}
                  onBuyNow={handleBuyNow}
                />
              </div>
            )}
          </div>
        ))}

        {isTyping && <TypingIndicator />}
      </div>

      {/* Sticky cart bar (shown after add-to-cart) */}
      {showCartBar && itemCount > 0 && (
        <div className="border-t border-green-200 bg-green-50 px-4 py-2 flex items-center justify-between">
          <span className="text-xs font-medium text-green-800">
            🛒 {itemCount} item{itemCount > 1 ? "s" : ""} in cart
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => router.push(ROUTES.CART)}
              className="rounded-lg bg-white border border-green-300 px-3 py-1 text-xs font-medium text-green-800 hover:bg-green-100 transition"
            >
              View Cart
            </button>
            <button
              onClick={() => router.push(ROUTES.CHECKOUT)}
              className="rounded-lg bg-green-600 px-3 py-1 text-xs font-semibold text-white hover:bg-green-700 transition"
            >
              Checkout
            </button>
          </div>
        </div>
      )}

      {/* Input */}
      <div className="border-t bg-slate-50 px-4 py-3 space-y-2">
        {isEmpty && <Suggestions onSelect={handleSuggestion} />}
        <ChatInput
          onSend={sendMessage}
          disabled={isTyping}
          autoSubmitVoice={true}
          placeholder={
            isTyping ? "Finding products..." :
            lastResult?.cart?.products?.length ? "Say 'add it', 'buy now', or search for more..." :
            "Say or type what you need..."
          }
        />
      </div>
    </div>
  );
}

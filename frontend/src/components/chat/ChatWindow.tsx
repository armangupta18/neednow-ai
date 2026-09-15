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
import { cn, formatPrice } from "@/lib/utils";
import { ShoppingBag, CheckCircle2, ArrowRight, X } from "lucide-react";

export default function ChatWindow() {
  const router = useRouter();
  const {
    messages,
    lastResult,
    isTyping,
    sendMessage,
    clearChat,
  } = useChat();

  const { addItem, itemCount, totalAmount } = useCart();
  const [toastItem, setToastItem] = useState<{ title: string; price?: number } | null>(null);
  const [cartBounced, setCartBounced] = useState(false);

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

  // Read aloud new assistant messages.
  useEffect(() => {
    if (messages.length > prevMessageCount.current) {
      const lastMsg = messages[messages.length - 1];
      if (lastMsg?.role === "assistant" && !lastMsg.metadata?.error) {
        const content = lastMsg.content;
        if (content && !content.startsWith("{") && !content.startsWith("[")) {
          speak(content);
        }
      }
    }
    prevMessageCount.current = messages.length;
  }, [messages, speak]);

  const handleSuggestion = (text: string) => {
    sendMessage(text);
  };

  const handleAddToCart = async (productId: string) => {
    const product = lastResult?.cart?.products?.find((p: { id: string }) => p.id === productId);
    const success = await addItem(productId);
    
    if (product || success) {
      // Trigger toast & bounce feedback
      setToastItem({
        title: product?.title || "Item",
        price: product?.price,
      });

      setCartBounced(true);
      setTimeout(() => setCartBounced(false), 600);

      // Auto dismiss toast after 3.5s
      setTimeout(() => {
        setToastItem((curr) => (curr?.title === (product?.title || "Item") ? null : curr));
      }, 3500);
    }
    return success;
  };

  const handleBuyNow = async () => {
    if (lastResult?.cart?.products?.[0]) {
      await addItem(lastResult.cart.products[0].id);
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
    <div className="relative flex h-full flex-col">
      {/* Floating Animated Toast on Add to Cart */}
      {toastItem && (
        <div className="absolute top-16 left-1/2 -translate-x-1/2 z-40 w-[92%] max-w-md animate-slide-in-down duration-300">
          <div className="flex items-center justify-between gap-3 rounded-xl border border-emerald-300 bg-emerald-950/90 p-3 shadow-xl backdrop-blur-md text-white">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400 ring-1 ring-emerald-400/40">
                <CheckCircle2 className="h-5 w-5 animate-checkmark-pop" />
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold text-emerald-300 flex items-center gap-1">
                  Added to Cart
                  {toastItem.price != null && (
                    <span className="text-emerald-100 font-normal">({formatPrice(toastItem.price)})</span>
                  )}
                </p>
                <p className="text-xs text-white truncate font-medium">
                  {toastItem.title}
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-1 shrink-0">
              <button
                onClick={() => router.push(ROUTES.CART)}
                className="flex items-center gap-1 rounded-lg bg-emerald-500 px-2.5 py-1 text-xs font-bold text-emerald-950 hover:bg-emerald-400 transition active:scale-95"
              >
                <span>View</span>
                <ArrowRight className="h-3 w-3" />
              </button>
              <button
                onClick={() => setToastItem(null)}
                className="rounded-lg p-1 text-emerald-300 hover:bg-emerald-800/50 transition"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between border-b px-4 py-3 bg-white/90 backdrop-blur-sm">
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

      {/* Sticky cart bar (animated whenever items are in cart) */}
      {itemCount > 0 && (
        <div className="border-t border-emerald-200 bg-gradient-to-r from-emerald-50 via-teal-50 to-emerald-50 px-4 py-2.5 flex items-center justify-between shadow-sm animate-slide-in-bottom">
          <div className="flex items-center gap-2">
            <div className={cn(
              "flex h-7 w-7 items-center justify-center rounded-full bg-emerald-600 text-white transition-transform duration-300",
              cartBounced && "animate-cart-bounce"
            )}>
              <ShoppingBag className="h-4 w-4" />
            </div>
            <div>
              <span className={cn(
                "inline-block text-xs font-bold text-emerald-950 transition-transform duration-200",
                cartBounced && "scale-110 text-emerald-600 font-extrabold"
              )}>
                {itemCount} item{itemCount > 1 ? "s" : ""} in cart
              </span>
              {totalAmount > 0 && (
                <span className="ml-1.5 text-xs text-emerald-700 font-medium">
                  ({formatPrice(totalAmount)})
                </span>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={() => router.push(ROUTES.CART)}
              className="rounded-lg bg-white border border-emerald-300 px-3 py-1.5 text-xs font-semibold text-emerald-800 hover:bg-emerald-100 transition active:scale-95 shadow-sm"
            >
              View Cart
            </button>
            <button
              onClick={() => router.push(ROUTES.CHECKOUT)}
              className="rounded-lg bg-emerald-600 px-3.5 py-1.5 text-xs font-bold text-white hover:bg-emerald-700 transition active:scale-95 shadow-sm hover:shadow"
            >
              Checkout →
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

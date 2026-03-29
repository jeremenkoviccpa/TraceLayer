"use client";

import { useEffect, useRef, useState } from "react";
import {
  Bot,
  Edit2,
  MessageSquare,
  MoreHorizontal,
  PanelRightClose,
  Plus,
  Send,
  Sparkles,
  Trash2,
} from "lucide-react";
import { api } from "@/lib/api";
import type { ChatConversation, ChatMessage } from "@/lib/types";

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export default function GlobalChat() {
  const [open, setOpen] = useState(false);
  const [conversations, setConversations] = useState<ChatConversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const [loadingConvs, setLoadingConvs] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [menuId, setMenuId] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const renameInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!open) return;
    setLoadingConvs(true);
    api
      .listConversations()
      .then((data) => {
        setConversations(data);
        if (!activeId && data.length > 0) loadConversation(data[0].id);
      })
      .catch(() => {})
      .finally(() => setLoadingConvs(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const loadConversation = async (id: string) => {
    setActiveId(id);
    setMessages([]);
    setLoadingMessages(true);
    try {
      const conv = await api.getConversation(id);
      setMessages(conv.messages);
    } catch {
      /* silent */
    } finally {
      setLoadingMessages(false);
    }
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinking]);

  useEffect(() => {
    if (open && activeId && inputRef.current) inputRef.current.focus();
  }, [open, activeId]);

  useEffect(() => {
    if (renamingId && renameInputRef.current) renameInputRef.current.focus();
  }, [renamingId]);

  const handleNewConversation = async () => {
    try {
      const conv = await api.createConversation();
      setConversations((p) => [conv, ...p]);
      setActiveId(conv.id);
      setMessages([]);
      setTimeout(() => inputRef.current?.focus(), 100);
    } catch {
      /* silent */
    }
  };

  const handleSend = async () => {
    if (!input.trim() || thinking || !activeId) return;
    const text = input.trim();
    setInput("");
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
    }

    const tempUser: ChatMessage = {
      id: `tmp-${Date.now()}`,
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((p) => [...p, tempUser]);
    setThinking(true);

    try {
      const [result] = await Promise.all([api.sendChatMessage(activeId, text), sleep(3000)]);
      setMessages((p) => {
        const without = p.filter((m) => m.id !== tempUser.id);
        return [
          ...without,
          { ...result.user_message, role: result.user_message.role as "user" | "assistant" },
          { ...result.assistant_message, role: result.assistant_message.role as "user" | "assistant" },
        ];
      });
      setConversations((p) =>
        p.map((c) =>
          c.id === activeId ? { ...c, title: result.conversation_title, updated_at: new Date().toISOString() } : c,
        ),
      );
    } catch {
      setMessages((p) => p.filter((m) => m.id !== tempUser.id));
    } finally {
      setThinking(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const startRename = (conv: ChatConversation) => {
    setRenamingId(conv.id);
    setRenameValue(conv.title);
    setMenuId(null);
  };

  const commitRename = async (id: string) => {
    if (!renameValue.trim()) { setRenamingId(null); return; }
    try {
      const updated = await api.renameConversation(id, renameValue.trim());
      setConversations((p) => p.map((c) => (c.id === id ? updated : c)));
    } catch {
      /* silent */
    } finally {
      setRenamingId(null);
    }
  };

  // Close menu when clicking outside (safer than a fixed backdrop which can intercept button clicks)
  useEffect(() => {
    if (!menuId) return;
    const handler = (e: MouseEvent) => {
      const target = e.target as Element;
      if (!target.closest("[data-menu]")) setMenuId(null);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [menuId]);

  const handleDelete = async (id: string) => {
    setMenuId(null);
    // Snapshot remaining BEFORE the async gap to avoid stale closure
    const remaining = conversations.filter((c) => c.id !== id);
    const wasActive = activeId === id;
    try {
      await api.deleteConversation(id);
      setConversations(remaining);
      if (wasActive) {
        setActiveId(null);
        setMessages([]);
        if (remaining.length > 0) loadConversation(remaining[0].id);
      }
    } catch {
      /* silent */
    }
  };

  const activeConv = conversations.find((c) => c.id === activeId);

  return (
    <>
      {/* ── Collapse tab (visible when closed) ── */}
      <button
        onClick={() => setOpen(true)}
        className={`fixed right-0 top-1/2 -translate-y-1/2 z-40 flex flex-col items-center justify-center gap-2
          w-9 bg-brand-600 hover:bg-brand-700 text-white rounded-l-2xl py-5
          shadow-lg shadow-brand-600/25 transition-all duration-300 hover:w-10
          ${open ? "opacity-0 pointer-events-none translate-x-2" : "opacity-100"}`}
        title="Open AI Advisor"
      >
        <Bot className="w-4 h-4 shrink-0" />
        <span
          className="text-[10px] font-bold tracking-widest uppercase"
          style={{ writingMode: "vertical-rl", transform: "rotate(180deg)", letterSpacing: "0.15em" }}
        >
          AI
        </span>
      </button>

      {/* ── Side panel ── */}
      <div
        className={`fixed top-0 right-0 bottom-0 z-50 flex flex-col bg-white border-l border-gray-200
          shadow-[−4px_0_24px_rgba(0,0,0,0.08)]
          transition-transform duration-300 ease-[cubic-bezier(0.32,0.72,0,1)]
          ${open ? "translate-x-0" : "translate-x-full"}
          w-[380px] max-w-[100vw]`}
      >
        {/* ── Header ── */}
        <div className="shrink-0 h-14 flex items-center gap-3 px-4 border-b border-gray-100">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shrink-0 shadow-sm shadow-brand-600/30">
            <Sparkles className="w-3.5 h-3.5 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[13px] font-semibold text-gray-900 leading-none truncate">
              {activeConv?.title ?? "AI Compliance Advisor"}
            </p>
            <p className="text-[10px] text-gray-400 mt-0.5">Powered by Llama 3.3 · Groq</p>
          </div>
          <button
            onClick={() => setOpen(false)}
            title="Collapse"
            className="flex items-center gap-1.5 pl-2 pr-3 py-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-700 transition-colors shrink-0 text-xs font-medium"
          >
            <PanelRightClose className="w-4 h-4" />
            <span className="hidden sm:inline">Close</span>
          </button>
        </div>

        {/* ── Conversation list ── */}
        <div className="shrink-0 border-b border-gray-100 bg-gray-50/50">
          {/* List header */}
          <div className="flex items-center justify-between px-4 pt-3 pb-1.5">
            <span className="text-[10px] font-semibold text-gray-400 uppercase tracking-widest">Conversations</span>
            <button
              onClick={handleNewConversation}
              className="inline-flex items-center gap-1 text-[11px] font-semibold text-brand-600 hover:text-brand-700 transition-colors"
            >
              <Plus className="w-3 h-3" />
              New
            </button>
          </div>

          {/* Items */}
          <div className="overflow-y-auto max-h-[168px] px-2 pb-2 space-y-0.5">
            {loadingConvs ? (
              <div className="flex justify-center py-4">
                <div className="w-4 h-4 border-2 border-brand-400 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : conversations.length === 0 ? (
              <div className="flex flex-col items-center py-5 gap-1.5">
                <MessageSquare className="w-5 h-5 text-gray-300" />
                <p className="text-xs text-gray-400">No conversations yet</p>
                <button
                  onClick={handleNewConversation}
                  className="text-xs text-brand-600 hover:text-brand-700 font-medium mt-0.5"
                >
                  Start one →
                </button>
              </div>
            ) : (
              conversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => { if (renamingId !== conv.id) loadConversation(conv.id); }}
                  className={`group relative flex items-center rounded-lg cursor-pointer transition-all
                    ${activeId === conv.id
                      ? "bg-brand-50 border border-brand-100"
                      : "hover:bg-white border border-transparent hover:border-gray-100 hover:shadow-sm"
                    }`}
                >
                  {renamingId === conv.id ? (
                    <input
                      ref={renameInputRef}
                      value={renameValue}
                      onChange={(e) => setRenameValue(e.target.value)}
                      onBlur={() => commitRename(conv.id)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") commitRename(conv.id);
                        if (e.key === "Escape") setRenamingId(null);
                      }}
                      onClick={(e) => e.stopPropagation()}
                      className="w-full px-3 py-2 text-xs bg-transparent outline-none text-gray-900 border-b border-brand-400"
                    />
                  ) : (
                    <div className="flex items-center w-full px-2.5 py-2 gap-1.5 min-w-0">
                      <span className={`flex-1 text-xs truncate leading-snug ${activeId === conv.id ? "font-medium text-brand-700" : "text-gray-600"}`}>
                        {conv.title}
                      </span>
                      <button
                        data-menu
                        onClick={(e) => { e.stopPropagation(); setMenuId(menuId === conv.id ? null : conv.id); }}
                        className="shrink-0 opacity-0 group-hover:opacity-100 w-5 h-5 flex items-center justify-center rounded-md hover:bg-gray-200 transition-all"
                      >
                        <MoreHorizontal className="w-3 h-3 text-gray-500" />
                      </button>
                    </div>
                  )}

                  {/* Dropdown — data-menu marks it so the outside-click handler ignores it */}
                  {menuId === conv.id && (
                    <div
                      data-menu
                      className="absolute right-1 top-8 z-[200] w-36 bg-white border border-gray-100 rounded-xl shadow-xl overflow-hidden"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <button
                        onClick={() => startRename(conv)}
                        className="flex items-center gap-2.5 w-full px-3 py-2.5 text-xs text-gray-700 hover:bg-gray-50 transition-colors"
                      >
                        <Edit2 className="w-3 h-3 text-gray-400" />
                        Rename
                      </button>
                      <div className="border-t border-gray-50" />
                      <button
                        onClick={() => handleDelete(conv.id)}
                        className="flex items-center gap-2.5 w-full px-3 py-2.5 text-xs text-red-500 hover:bg-red-50 transition-colors"
                      >
                        <Trash2 className="w-3 h-3" />
                        Delete
                      </button>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* ── Messages ── */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
          {!activeId ? (
            <div className="flex flex-col items-center justify-center h-full text-center gap-4 px-6">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-50 to-brand-100 flex items-center justify-center">
                <Bot className="w-7 h-7 text-brand-500" />
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-800">Ask me anything</p>
                <p className="text-xs text-gray-400 mt-1 leading-relaxed">
                  Frameworks, evidence gaps, audit prep, policies — I know your compliance stack.
                </p>
              </div>
              <button
                onClick={handleNewConversation}
                className="inline-flex items-center gap-1.5 bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold px-4 py-2 rounded-xl transition-colors shadow-sm shadow-brand-600/20"
              >
                <Plus className="w-3.5 h-3.5" />
                Start conversation
              </button>
            </div>
          ) : loadingMessages ? (
            <div className="flex justify-center pt-10">
              <div className="w-5 h-5 border-2 border-brand-400 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full gap-2 text-center">
              <MessageSquare className="w-6 h-6 text-gray-200" />
              <p className="text-xs text-gray-400">Send a message to get started</p>
            </div>
          ) : (
            messages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} group`}>
                {msg.role === "assistant" && (
                  <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shrink-0 mt-0.5 mr-2 shadow-sm shadow-brand-600/20">
                    <Sparkles className="w-3 h-3 text-white" />
                  </div>
                )}
                <div
                  className={`max-w-[78%] rounded-2xl px-3.5 py-2.5 text-[13px] leading-relaxed whitespace-pre-wrap
                    ${msg.role === "user"
                      ? "bg-brand-600 text-white rounded-br-sm shadow-sm shadow-brand-600/20"
                      : "bg-gray-100 text-gray-800 rounded-bl-sm"
                    }`}
                >
                  {msg.content}
                </div>
              </div>
            ))
          )}

          {thinking && (
            <div className="flex justify-start">
              <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shrink-0 mt-0.5 mr-2 shadow-sm shadow-brand-600/20">
                <Sparkles className="w-3 h-3 text-white" />
              </div>
              <div className="bg-gray-100 rounded-2xl rounded-bl-sm px-3.5 py-2.5 flex items-center gap-1.5">
                <span className="text-[13px] text-gray-400">Thinking</span>
                <span className="flex gap-0.5 ml-0.5">
                  {[0, 1, 2].map((i) => (
                    <span
                      key={i}
                      className="w-1 h-1 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: `${i * 160}ms` }}
                    />
                  ))}
                </span>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* ── Input ── */}
        {activeId && (
          <div className="shrink-0 p-3 border-t border-gray-100 bg-white">
            <div className="flex items-end gap-2 rounded-xl border border-gray-200 bg-gray-50 px-3 py-2
              focus-within:border-brand-400 focus-within:bg-white focus-within:ring-2 focus-within:ring-brand-100
              transition-all duration-150">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                onInput={(e) => {
                  const el = e.currentTarget;
                  el.style.height = "auto";
                  el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
                }}
                placeholder="Ask about compliance, gaps, frameworks…"
                rows={1}
                disabled={thinking}
                className="flex-1 bg-transparent text-[13px] text-gray-900 placeholder-gray-400 resize-none outline-none
                  leading-relaxed disabled:opacity-50 max-h-[120px]"
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || thinking}
                className="w-7 h-7 rounded-lg bg-brand-600 hover:bg-brand-700 disabled:opacity-30 text-white
                  flex items-center justify-center shrink-0 transition-all hover:scale-105 active:scale-95 shadow-sm shadow-brand-600/20"
              >
                <Send className="w-3.5 h-3.5" />
              </button>
            </div>
            <p className="text-[10px] text-gray-300 text-center mt-2">Enter to send · Shift+Enter for new line</p>
          </div>
        )}

        {/* ── No active conversation input ── */}
        {!activeId && !loadingConvs && (
          <div className="shrink-0 p-3 border-t border-gray-100">
            <button
              onClick={handleNewConversation}
              className="w-full flex items-center justify-center gap-2 rounded-xl border-2 border-dashed border-gray-200
                hover:border-brand-300 hover:bg-brand-50/30 text-gray-400 hover:text-brand-600
                py-3 text-xs font-medium transition-all duration-150"
            >
              <Plus className="w-3.5 h-3.5" />
              New conversation
            </button>
          </div>
        )}
      </div>

      {/* ── Backdrop (mobile) ── */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/20 backdrop-blur-[2px] md:hidden"
          onClick={() => setOpen(false)}
        />
      )}
    </>
  );
}

"use client";

import { useEffect, useRef, useState } from "react";
import {
  Bot,
  ChevronLeft,
  ChevronRight,
  Edit2,
  MessageSquare,
  MoreHorizontal,
  Plus,
  Send,
  Trash2,
  X,
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

  // Load conversations when panel opens
  useEffect(() => {
    if (!open) return;
    setLoadingConvs(true);
    api.listConversations()
      .then((data) => {
        setConversations(data);
        if (!activeId && data.length > 0) {
          loadConversation(data[0].id);
        }
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
      // silent
    } finally {
      setLoadingMessages(false);
    }
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinking]);

  useEffect(() => {
    if (open && inputRef.current) inputRef.current.focus();
  }, [open, activeId]);

  useEffect(() => {
    if (renamingId && renameInputRef.current) renameInputRef.current.focus();
  }, [renamingId]);

  const handleNewConversation = async () => {
    try {
      const conv = await api.createConversation();
      setConversations((prev) => [conv, ...prev]);
      setActiveId(conv.id);
      setMessages([]);
    } catch {
      // silent
    }
  };

  const handleSend = async () => {
    if (!input.trim() || thinking || !activeId) return;
    const text = input.trim();
    setInput("");

    const tempUser: ChatMessage = {
      id: `tmp-u-${Date.now()}`,
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUser]);
    setThinking(true);

    try {
      const [result] = await Promise.all([
        api.sendChatMessage(activeId, text),
        sleep(3000),
      ]);
      setMessages((prev) => {
        const without = prev.filter((m) => m.id !== tempUser.id);
        return [
          ...without,
          { ...result.user_message, role: result.user_message.role as "user" | "assistant" },
          { ...result.assistant_message, role: result.assistant_message.role as "user" | "assistant" },
        ];
      });
      // Update conversation title if it was auto-titled
      setConversations((prev) =>
        prev.map((c) =>
          c.id === activeId ? { ...c, title: result.conversation_title, updated_at: new Date().toISOString() } : c,
        ),
      );
    } catch {
      setMessages((prev) => prev.filter((m) => m.id !== tempUser.id));
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
    if (!renameValue.trim()) {
      setRenamingId(null);
      return;
    }
    try {
      const updated = await api.renameConversation(id, renameValue.trim());
      setConversations((prev) => prev.map((c) => (c.id === id ? updated : c)));
    } catch {
      // silent
    } finally {
      setRenamingId(null);
    }
  };

  const handleDelete = async (id: string) => {
    setMenuId(null);
    try {
      await api.deleteConversation(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (activeId === id) {
        setActiveId(null);
        setMessages([]);
        const remaining = conversations.filter((c) => c.id !== id);
        if (remaining.length > 0) loadConversation(remaining[0].id);
      }
    } catch {
      // silent
    }
  };

  const activeConv = conversations.find((c) => c.id === activeId);

  return (
    <>
      {/* Toggle button — fixed bottom-right */}
      <button
        onClick={() => setOpen((o) => !o)}
        className="fixed bottom-5 right-5 z-50 w-12 h-12 bg-brand-600 hover:bg-brand-700 text-white rounded-full shadow-lg shadow-brand-600/30 flex items-center justify-center transition-all hover:scale-105 active:scale-95"
        title="AI Compliance Advisor"
      >
        {open ? <X className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
      </button>

      {/* Chat panel */}
      {open && (
        <div className="fixed bottom-20 right-5 z-50 w-[760px] max-w-[calc(100vw-40px)] h-[580px] bg-white rounded-2xl border border-gray-200 shadow-2xl flex overflow-hidden">
          {/* Sidebar — conversation list */}
          <div className="w-56 shrink-0 border-r border-gray-100 flex flex-col bg-gray-50/60">
            {/* Header */}
            <div className="flex items-center justify-between px-3 py-3 border-b border-gray-100">
              <span className="text-xs font-semibold text-gray-600 uppercase tracking-wider">Chats</span>
              <button
                onClick={handleNewConversation}
                className="w-6 h-6 rounded-lg bg-brand-600 hover:bg-brand-700 text-white flex items-center justify-center transition-colors"
                title="New chat"
              >
                <Plus className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto py-1">
              {loadingConvs ? (
                <div className="flex justify-center pt-8">
                  <div className="w-4 h-4 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
                </div>
              ) : conversations.length === 0 ? (
                <div className="px-3 pt-8 text-center">
                  <MessageSquare className="w-6 h-6 text-gray-300 mx-auto mb-2" />
                  <p className="text-xs text-gray-400">No conversations yet</p>
                  <button
                    onClick={handleNewConversation}
                    className="mt-3 text-xs text-brand-600 hover:text-brand-700 font-medium"
                  >
                    Start one
                  </button>
                </div>
              ) : (
                conversations.map((conv) => (
                  <div
                    key={conv.id}
                    className={`group relative mx-1 rounded-lg cursor-pointer transition-colors ${
                      activeId === conv.id
                        ? "bg-white shadow-sm border border-gray-100"
                        : "hover:bg-white/70"
                    }`}
                    onClick={() => { if (renamingId !== conv.id) loadConversation(conv.id); }}
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
                        className="w-full px-2 py-2 text-xs text-gray-900 bg-transparent outline-none border-b border-brand-400"
                      />
                    ) : (
                      <div className="flex items-center gap-1 px-2 py-2">
                        <span className="flex-1 text-xs text-gray-700 truncate leading-snug">
                          {conv.title}
                        </span>
                        {/* Three-dot menu */}
                        <button
                          onClick={(e) => { e.stopPropagation(); setMenuId(menuId === conv.id ? null : conv.id); }}
                          className="shrink-0 opacity-0 group-hover:opacity-100 w-5 h-5 flex items-center justify-center rounded hover:bg-gray-200 transition-all"
                        >
                          <MoreHorizontal className="w-3 h-3 text-gray-500" />
                        </button>
                      </div>
                    )}

                    {/* Dropdown menu */}
                    {menuId === conv.id && (
                      <>
                        <div className="fixed inset-0 z-10" onClick={() => setMenuId(null)} />
                        <div className="absolute right-0 top-7 z-20 w-32 bg-white border border-gray-100 rounded-xl shadow-lg overflow-hidden">
                          <button
                            onClick={(e) => { e.stopPropagation(); startRename(conv); }}
                            className="flex items-center gap-2 w-full px-3 py-2 text-xs text-gray-700 hover:bg-gray-50"
                          >
                            <Edit2 className="w-3 h-3" />
                            Rename
                          </button>
                          <button
                            onClick={(e) => { e.stopPropagation(); handleDelete(conv.id); }}
                            className="flex items-center gap-2 w-full px-3 py-2 text-xs text-red-600 hover:bg-red-50"
                          >
                            <Trash2 className="w-3 h-3" />
                            Delete
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Main chat area */}
          <div className="flex-1 flex flex-col min-w-0">
            {/* Header */}
            <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-100 shrink-0">
              <Bot className="w-4 h-4 text-brand-600 shrink-0" />
              <span className="text-sm font-semibold text-gray-900 truncate">
                {activeConv?.title ?? "AI Compliance Advisor"}
              </span>
              <button
                onClick={() => setOpen(false)}
                className="ml-auto text-gray-400 hover:text-gray-600 transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
              {!activeId ? (
                <div className="flex flex-col items-center justify-center h-full text-center gap-3">
                  <Bot className="w-10 h-10 text-brand-200" />
                  <p className="text-sm text-gray-500 max-w-xs">
                    Your AI compliance advisor. Ask about frameworks, evidence gaps, policies, audit prep — anything compliance-related.
                  </p>
                  <button
                    onClick={handleNewConversation}
                    className="mt-1 inline-flex items-center gap-1.5 text-sm text-brand-600 hover:text-brand-700 font-medium"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    New conversation
                  </button>
                </div>
              ) : loadingMessages ? (
                <div className="flex justify-center pt-8">
                  <div className="w-5 h-5 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
                </div>
              ) : messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center gap-2">
                  <p className="text-sm text-gray-400">Start the conversation below</p>
                </div>
              ) : (
                messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[82%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${
                        msg.role === "user"
                          ? "bg-brand-600 text-white rounded-br-sm"
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
                  <div className="bg-gray-100 rounded-2xl rounded-bl-sm px-3.5 py-2.5">
                    <span className="flex items-center gap-1.5 text-sm text-gray-400 italic">
                      Thinking
                      <span className="flex gap-0.5 mt-0.5">
                        {[0, 1, 2].map((i) => (
                          <span
                            key={i}
                            className="w-1 h-1 bg-gray-400 rounded-full animate-bounce"
                            style={{ animationDelay: `${i * 150}ms` }}
                          />
                        ))}
                      </span>
                    </span>
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            {/* Input */}
            {activeId && (
              <div className="shrink-0 border-t border-gray-100 px-3 py-2.5">
                <div className="flex items-end gap-2 bg-gray-50 rounded-xl border border-gray-200 px-3 py-2 focus-within:border-brand-400 focus-within:ring-1 focus-within:ring-brand-200 transition-all">
                  <textarea
                    ref={inputRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask about compliance, frameworks, evidence gaps…"
                    rows={1}
                    disabled={thinking}
                    className="flex-1 bg-transparent text-sm text-gray-900 placeholder-gray-400 resize-none outline-none max-h-28 disabled:opacity-60"
                    style={{ lineHeight: "1.5" }}
                    onInput={(e) => {
                      const el = e.currentTarget;
                      el.style.height = "auto";
                      el.style.height = `${Math.min(el.scrollHeight, 112)}px`;
                    }}
                  />
                  <button
                    onClick={handleSend}
                    disabled={!input.trim() || thinking}
                    className="w-7 h-7 bg-brand-600 hover:bg-brand-700 disabled:opacity-40 text-white rounded-lg flex items-center justify-center shrink-0 transition-colors"
                  >
                    <Send className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}

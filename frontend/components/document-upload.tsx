"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { Document } from "@/lib/types";
import { Paperclip, Upload, Trash2, FileText, X, ExternalLink } from "lucide-react";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface DocumentUploadProps {
  resourceType: string;
  resourceId: string;
  label?: string;
}

export function DocumentUpload({ resourceType, resourceId, label = "Attachments" }: DocumentUploadProps) {
  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const load = useCallback(async () => {
    try {
      const data = await api.getDocuments(resourceType, resourceId);
      setDocs(data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [resourceType, resourceId]);

  useEffect(() => { load(); }, [load]);

  const upload = async (file: File) => {
    if (file.size > 50 * 1024 * 1024) {
      setError("File too large (max 50 MB)");
      return;
    }
    setUploading(true);
    setError(null);
    try {
      const doc = await api.uploadDocument(file, resourceType, resourceId);
      setDocs((prev) => [doc, ...prev]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleFiles = (files: FileList | null) => {
    if (!files?.length) return;
    upload(files[0]);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  const handleDelete = async (id: string) => {
    await api.deleteDocument(id).catch(() => {});
    setDocs((prev) => prev.filter((d) => d.id !== id));
    setDeletingId(null);
  };

  const handleDownload = async (id: string, filename: string) => {
    try {
      const { url } = await api.getDocumentUrl(id);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.target = "_blank";
      a.click();
    } catch {
      // ignore
    }
  };

  return (
    <div className="mt-4 pt-4 border-t border-gray-100">
      <div className="flex items-center gap-2 mb-3">
        <Paperclip className="w-3.5 h-3.5 text-gray-400" />
        <span className="text-xs font-semibold text-gray-600">{label}</span>
        {docs.length > 0 && (
          <span className="text-[10px] font-semibold text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded-full">
            {docs.length}
          </span>
        )}
      </div>

      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-xl px-4 py-3 text-center cursor-pointer transition-colors ${
          dragging ? "border-brand-400 bg-brand-50/50" : "border-gray-200 hover:border-gray-300 hover:bg-gray-50/50"
        }`}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
          accept="*/*"
        />
        {uploading ? (
          <div className="flex items-center justify-center gap-2">
            <div className="w-3.5 h-3.5 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-xs text-gray-400">Uploading…</span>
          </div>
        ) : (
          <div className="flex items-center justify-center gap-1.5">
            <Upload className="w-3.5 h-3.5 text-gray-300" />
            <span className="text-xs text-gray-400">
              <span className="font-semibold text-gray-500">Click to upload</span> or drag & drop
            </span>
          </div>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-2 mt-2 text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2">
          <X className="w-3 h-3 shrink-0" />
          {error}
          <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-600"><X className="w-3 h-3" /></button>
        </div>
      )}

      {/* File list */}
      {loading ? (
        <div className="mt-2 space-y-1.5">
          {[0, 1].map((i) => <div key={i} className="h-8 bg-gray-100 rounded-lg animate-pulse" />)}
        </div>
      ) : docs.length > 0 ? (
        <div className="mt-2 space-y-1">
          {docs.map((doc) => (
            <div key={doc.id} className="flex items-center gap-2 px-3 py-1.5 bg-gray-50 hover:bg-gray-100 rounded-lg group transition-colors">
              <FileText className="w-3.5 h-3.5 text-gray-400 shrink-0" />
              <button
                onClick={() => handleDownload(doc.id, doc.filename)}
                className="flex-1 min-w-0 text-left"
              >
                <p className="text-xs font-medium text-gray-700 truncate">{doc.filename}</p>
                <p className="text-[10px] text-gray-400">{formatBytes(doc.file_size)}</p>
              </button>
              <button
                onClick={() => handleDownload(doc.id, doc.filename)}
                className="text-gray-300 hover:text-gray-500 p-0.5 opacity-0 group-hover:opacity-100 transition-opacity"
                title="Download"
              >
                <ExternalLink className="w-3 h-3" />
              </button>
              {deletingId === doc.id ? (
                <div className="flex items-center gap-1">
                  <button onClick={() => setDeletingId(null)} className="text-[10px] text-gray-400 hover:text-gray-600 px-1.5 py-0.5 rounded">Cancel</button>
                  <button onClick={() => handleDelete(doc.id)} className="text-[10px] font-semibold text-white bg-red-500 hover:bg-red-600 px-1.5 py-0.5 rounded">Delete</button>
                </div>
              ) : (
                <button
                  onClick={() => setDeletingId(doc.id)}
                  className="text-gray-200 hover:text-red-400 p-0.5 opacity-0 group-hover:opacity-100 transition-all"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              )}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

import type { ParseResponse } from "./types";

const API_BASE = "http://localhost:8000/api";

export async function parseContent(content: string): Promise<ParseResponse> {
  const res = await fetch(`${API_BASE}/parse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  
  if (!res.ok) {
    throw new Error(`Parse failed: ${res.statusText}`);
  }
  
  return res.json();
}

export async function exportDocument(
  document: any,
  theme: "modern" | "academic" | "corporate" | "minimal" = "modern"
): Promise<void> {
  const res = await fetch(`${API_BASE}/export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document, theme }),
  });

  if (!res.ok) {
    throw new Error(`Export failed: ${res.statusText}`);
  }

  // Download the blob
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = window.document.createElement("a");
  a.href = url;
  a.download = "document.docx";
  window.document.body.appendChild(a);
  a.click();
  window.document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}

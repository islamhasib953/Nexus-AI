const base = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");
export type Principal = { user_id: string; organization_id: string; role: string; workspace: string };
export type Conversation = { id: string; title: string; workspace: string; created_at: string; updated_at: string };
export type Message = { id: string; role: "user" | "assistant"; content: string; created_at: string };
export type ConversationDetail = Conversation & { messages: Message[] };
export type Run = { id: string; conversation_id: string; status: string; events_url: string };
export type Approval = { id: string; action_type: string; status: string; expires_at: string };
export type OperationsOverview = {
  generated_at: string;
  window_hours: number;
  organization_id: string;
  summary: { runs_total: number; runs_failed: number; run_error_rate: number; queue_depth: number; queue_oldest_seconds: number; run_duration_avg_ms: number; tool_calls_total: number; tool_failure_rate: number; cache_hit_rate: number; routing_latency_avg_ms: number; documents_indexed_chunks: number };
  cost: { estimated_usd: string; by_provider: Record<string, string>; by_model: Record<string, string>; by_agent: Record<string, string>; by_task: Record<string, string> };
  providers: { provider: string; available: boolean; consecutive_failures: number; unhealthy_until: string | null }[];
};
const storage = typeof sessionStorage === "undefined" ? null : sessionStorage;
let token = storage?.getItem("nexus_access_token") ?? "";
export function setAccessToken(value: string) { token = value; storage?.setItem("nexus_access_token", value); }
export function clearAccessToken() { token = ""; storage?.removeItem("nexus_access_token"); }
async function request<T>(path: string, init: RequestInit = {}): Promise<T> { const response = await fetch(`${base}${path}`, { ...init, headers: { Accept: "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...init.headers } }); if (!response.ok) throw new Error((await response.json().catch(() => null))?.error?.message ?? `Request failed (${response.status})`); return response.json() as Promise<T>; }
export function login(profile: "internal" | "customer" | "other") { return request<{ access_token: string }>("/api/v1/auth/dev/session", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ profile }) }); }
export function getMe() { return request<Principal>("/api/v1/me"); }
export function listConversations() { return request<{ items: Conversation[] }>("/api/v1/conversations"); }
export function createConversation(title: string) { return request<Conversation>("/api/v1/conversations", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ title }) }); }
export function getConversation(id: string) { return request<ConversationDetail>(`/api/v1/conversations/${id}`); }
export function createRun(id: string, content: string) { return request<Run>(`/api/v1/conversations/${id}/runs`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ content }) }); }
export function cancelRun(id: string) { return request<Run>(`/api/v1/runs/${id}/cancel`, { method: "POST" }); }
export function listApprovals() { return request<{ items: Approval[] }>("/api/v1/approvals"); }
export function approveApproval(id: string) { return request<{ id: string; status: string }>(`/api/v1/approvals/${id}/approve`, { method: "POST" }); }
export function cancelApproval(id: string) { return request<{ id: string; status: string }>(`/api/v1/approvals/${id}/cancel`, { method: "POST" }); }
export function getOperationsOverview() { return request<OperationsOverview>("/api/v1/operations/overview"); }
export async function streamRun(run: Run, onEvent: (type: string, data: Record<string, unknown>) => void) { const response = await fetch(`${base}${run.events_url}`, { headers: { Accept: "text/event-stream", Authorization: `Bearer ${token}` } }); if (!response.ok || !response.body) throw new Error("Unable to open response stream."); const reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer = ""; while (true) { const { value, done } = await reader.read(); if (done) break; buffer += decoder.decode(value, { stream: true }); const records = buffer.split("\n\n"); buffer = records.pop() ?? ""; for (const record of records) { const type = record.match(/^event: (.+)$/m)?.[1] ?? "message"; const raw = record.match(/^data: (.+)$/m)?.[1]; if (raw) onEvent(type, JSON.parse(raw) as Record<string, unknown>); } } }

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function startAnalysis(url: string): Promise<{ task_id: string }> {
  const res = await fetch(`${API_URL}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  if (!res.ok) throw new Error(`Failed to start analysis: ${res.statusText}`);
  return res.json();
}

export async function getResults(taskId: string) {
  const res = await fetch(`${API_URL}/api/results/${taskId}`);
  if (!res.ok) throw new Error(`Failed to get results: ${res.statusText}`);
  return res.json();
}

export function getVideoUrl(taskId: string): string {
  return `${API_URL}/api/video/${taskId}`;
}

export function getFrameUrl(taskId: string, framePath: string): string {
  const filename = framePath.split("/").pop();
  return `${API_URL}/api/frame/${taskId}/${filename}`;
}

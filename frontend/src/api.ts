import type { Candidate, Location, PointResponse, SearchResult } from "./types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, options);
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export async function searchPlaces(query: string): Promise<SearchResult[]> {
  return request(`/api/v1/geo/search?q=${encodeURIComponent(query)}`);
}

export async function analyzePoint(location: Location): Promise<PointResponse> {
  return request("/api/v1/analysis/point", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ business_type: "coffee_shop", ...location, radius_m: 1000 }),
  });
}

export async function analyzeArea(bounds: {
  south: number; west: number; north: number; east: number;
}): Promise<Candidate[]> {
  const response = await request<{ candidates: Candidate[] }>("/api/v1/analysis/area", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ business_type: "coffee_shop", bounds, grid_spacing_m: 500, top_n: 20 }),
  });
  return response.candidates;
}


/**
 * FAISS / Vector Search helpers for NeedNow AI frontend.
 *
 * Client-side utilities for interacting with the vector search
 * backend (ChromaDB/FAISS). All actual vector operations happen
 * server-side — this module provides typed request builders and
 * result parsers.
 */

import { apiPost, apiGet } from "./api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface VectorSearchResult {
  id: string;
  title: string;
  category: string;
  rating: number;
  similarity_score: number;
  metadata: Record<string, unknown>;
}

export interface VectorSearchRequest {
  query: string;
  top_k?: number;
  category?: string;
  min_rating?: number;
}

export interface VectorSearchResponse {
  results: VectorSearchResult[];
  query: string;
  total_found: number;
}

export interface VectorStats {
  total_vectors: number;
  collections: string[];
}

// ---------------------------------------------------------------------------
// API Functions
// ---------------------------------------------------------------------------

/**
 * Search for similar products via the vector store backend.
 * The backend converts the query text to an embedding and searches ChromaDB.
 */
export async function searchProducts(
  request: VectorSearchRequest
): Promise<VectorSearchResponse> {
  return apiPost<VectorSearchResponse>("/search/products", request);
}

/**
 * Get vector store statistics (total embeddings, collections).
 */
export async function getVectorStats(): Promise<VectorStats> {
  return apiGet<VectorStats>("/search/stats");
}

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

/** Convert a cosine distance to a similarity percentage (0-100) */
export function distanceToSimilarity(distance: number): number {
  return Math.round((1 - distance) * 100);
}

/** Format similarity score for display */
export function formatSimilarity(score: number): string {
  const pct = Math.round(score * 100);
  if (pct >= 90) return `${pct}% — Excellent match`;
  if (pct >= 70) return `${pct}% — Good match`;
  if (pct >= 50) return `${pct}% — Moderate match`;
  return `${pct}% — Weak match`;
}

/** Get color class for similarity score */
export function similarityColor(score: number): string {
  if (score >= 0.9) return "text-green-600";
  if (score >= 0.7) return "text-blue-600";
  if (score >= 0.5) return "text-amber-600";
  return "text-slate-400";
}

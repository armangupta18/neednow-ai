/**
 * Sustainability Service — connects to eco scoring and recommendation APIs.
 */

import { apiPost, apiGet } from "@/lib/api";
import { API_ROUTES } from "@/constants/routes";
import type { EcoAlternative, SustainabilityResponse } from "@/types/agent";
import type { ProductEcoScore } from "@/types/product";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface SustainabilityReportResponse {
  eco_alternatives: EcoAlternative[];
  total_carbon_saved: number;
  overall_sustainability_score: number;
}

export interface SustainabilityRecommendResponse {
  recommendations: EcoAlternative[];
  total_carbon_saved: number;
  overall_sustainability_score: number;
}

// ---------------------------------------------------------------------------
// API Functions
// ---------------------------------------------------------------------------

/** Get eco score for a single product */
export async function getProductEcoScore(
  productId: string
): Promise<ProductEcoScore> {
  return apiGet<ProductEcoScore>(API_ROUTES.SUSTAINABILITY.SCORE(productId));
}

/** Get eco-friendly alternative recommendations for products */
export async function getEcoRecommendations(
  productIds: string[]
): Promise<SustainabilityRecommendResponse> {
  return apiPost<SustainabilityRecommendResponse>(
    API_ROUTES.SUSTAINABILITY.RECOMMEND,
    { product_ids: productIds }
  );
}

/** Generate a full sustainability report for products */
export async function generateSustainabilityReport(
  productIds: string[]
): Promise<SustainabilityReportResponse> {
  return apiPost<SustainabilityReportResponse>(
    API_ROUTES.SUSTAINABILITY.ANALYZE,
    { product_ids: productIds }
  );
}

// ---------------------------------------------------------------------------
// Batch Operations
// ---------------------------------------------------------------------------

/** Get eco scores for multiple products */
export async function batchGetEcoScores(
  productIds: string[]
): Promise<Map<string, ProductEcoScore>> {
  const results = new Map<string, ProductEcoScore>();

  // Process in parallel (max 5 concurrent)
  const chunks = chunkArray(productIds, 5);
  for (const chunk of chunks) {
    const scores = await Promise.allSettled(
      chunk.map((id) => getProductEcoScore(id))
    );
    scores.forEach((result, idx) => {
      if (result.status === "fulfilled") {
        results.set(chunk[idx]!, result.value);
      }
    });
  }

  return results;
}

// ---------------------------------------------------------------------------
// Display Helpers
// ---------------------------------------------------------------------------

/** Get sustainability rating label from score */
export function getSustainabilityLabel(score: number): string {
  if (score >= 80) return "Excellent";
  if (score >= 60) return "Good";
  if (score >= 40) return "Fair";
  if (score >= 20) return "Low";
  return "Poor";
}

/** Get Tailwind color class for sustainability score */
export function getSustainabilityColor(score: number): string {
  if (score >= 80) return "text-green-600";
  if (score >= 60) return "text-emerald-600";
  if (score >= 40) return "text-amber-600";
  if (score >= 20) return "text-orange-600";
  return "text-red-500";
}

/** Format carbon savings for display */
export function formatCarbonSaved(kg: number): string {
  if (kg >= 1) return `${kg.toFixed(1)} kg CO₂ saved`;
  return `${(kg * 1000).toFixed(0)} g CO₂ saved`;
}

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

function chunkArray<T>(arr: T[], size: number): T[][] {
  const chunks: T[][] = [];
  for (let i = 0; i < arr.length; i += size) {
    chunks.push(arr.slice(i, i + size));
  }
  return chunks;
}

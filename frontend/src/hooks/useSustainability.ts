"use client";

import { useState, useCallback } from "react";
import { getProductEcoScore, getEcoRecommendations } from "@/services/sustainabilityApi";
import type { ProductEcoScore, SustainabilityRecommendResponse } from "@/services/sustainabilityApi";

export function useSustainability() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getScore = useCallback(async (productId: string): Promise<ProductEcoScore | null> => {
    try {
      setLoading(true);
      return await getProductEcoScore(productId);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to get eco score");
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const getRecommendations = useCallback(async (productIds: string[]): Promise<SustainabilityRecommendResponse | null> => {
    try {
      setLoading(true);
      return await getEcoRecommendations(productIds);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to get recommendations");
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { loading, error, getScore, getRecommendations };
}

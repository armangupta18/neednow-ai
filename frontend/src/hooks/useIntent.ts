"use client";

import { useState } from "react";

import api from "@/services/api";

import { IntentResponse } from "@/types/response";

export function useIntent() {
  const [loading, setLoading] = useState(false);

  const [data, setData] = useState<IntentResponse | null>(null);

  const [error, setError] = useState<string | null>(null);

  const generateCart = async (text: string) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.post("/intent", {
        text,
        user_id: "550e8400-e29b-41d4-a716-446655440000",
      });

      setData(response.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return {
    loading,
    error,
    data,
    generateCart,
  };
}

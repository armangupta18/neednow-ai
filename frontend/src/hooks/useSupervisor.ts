"use client";

import { useState } from "react";
import api from "@/services/api";
import { ENDPOINTS } from "@/constants/api";

export function useSupervisor() {
  const [loading, setLoading] = useState(false);

  const generateCart = async (situation: string) => {
    try {
      setLoading(true);
      // Uses the centralized Axios client — resolves to NEXT_PUBLIC_API_URL + /api/v1/intent
      const response = await api.post(ENDPOINTS.INTENT, {
        user_id: "550e8400-e29b-41d4-a716-446655440000",
        text: situation,
      });
      return response.data;
    } finally {
      setLoading(false);
    }
  };

  return { loading, generateCart };
}

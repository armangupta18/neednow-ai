import { create } from "zustand";
import { SupervisorResponse } from "@/types/recommendation";

interface RecommendationState {
  result: SupervisorResponse | null;

  setResult: (data: SupervisorResponse) => void;

  clearResult: () => void;
}

export const useRecommendationStore = create<RecommendationState>((set) => ({
  result: null,

  setResult: (data) =>
    set({
      result: data,
    }),

  clearResult: () =>
    set({
      result: null,
    }),
}));

import api from "./api";
import { ENDPOINTS } from "@/constants/api";

export interface EcoAlternative {
  original_product_id: string;
  original_product_name: string;
  alternative_product_id: string;
  alternative_product_name: string;
  carbon_saved: number;
  price_difference: number;
  sustainability_score: number;
}

export interface SustainabilityRecommendResponse {
  recommendations: EcoAlternative[];
  total_carbon_saved: number;
  overall_sustainability_score: number;
}

export interface ProductEcoScore {
  product_id: string;
  product_name: string;
  category: string;
  sustainability_score: number;
}

export async function getProductEcoScore(productId: string) {
  const response = await api.get<ProductEcoScore>(ENDPOINTS.SUSTAINABILITY.SCORE(productId));
  return response.data;
}

export async function getEcoRecommendations(productIds: string[]) {
  const response = await api.post<SustainabilityRecommendResponse>(
    ENDPOINTS.SUSTAINABILITY.RECOMMEND,
    { product_ids: productIds }
  );
  return response.data;
}

/**
 * Product types — maps to backend Product model and search results.
 */

// ---------------------------------------------------------------------------
// Core Product (from PostgreSQL)
// ---------------------------------------------------------------------------

export interface Product {
  id: string;
  title: string;
  description: string;
  category: string;
  brand: string | null;
  price: number;
  stock: number;
  image_url: string | null;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Product in Recommendation Context
// ---------------------------------------------------------------------------

/** Product as returned in supervisor cart.products[] */
export interface RecommendedProduct {
  id: string;
  title: string;
  price: number;
  score: number;
}

/** Bundle product suggestion */
export interface BundleProduct {
  id: string;
  title: string;
  price: number;
}

// ---------------------------------------------------------------------------
// Product Search
// ---------------------------------------------------------------------------

export interface ProductSearchRequest {
  query: string;
  top_k?: number;
  category?: string;
  min_rating?: number;
}

export interface ProductSearchResult {
  id: string;
  title: string;
  category: string;
  rating: number;
  similarity_score: number;
  metadata: Record<string, unknown>;
}

export interface ProductSearchResponse {
  results: ProductSearchResult[];
  query: string;
  total_found: number;
}

// ---------------------------------------------------------------------------
// Sustainability Score
// ---------------------------------------------------------------------------

export interface ProductEcoScore {
  product_id: string;
  product_name: string;
  category: string;
  sustainability_score: number;
}

export interface SustainabilityScoreBreakdown {
  parent_asin: string;
  recyclable: number;
  reusable: number;
  eco_friendly: number;
  energy_efficient: number;
  sustainable_packaging: number;
  overall_score: number;
}

// ---------------------------------------------------------------------------
// Product Display Helpers
// ---------------------------------------------------------------------------

export type StockStatus = "in_stock" | "low_stock" | "out_of_stock";

export function getStockStatus(stock: number): StockStatus {
  if (stock <= 0) return "out_of_stock";
  if (stock <= 5) return "low_stock";
  return "in_stock";
}

export function getStockLabel(status: StockStatus): string {
  switch (status) {
    case "in_stock": return "In Stock";
    case "low_stock": return "Low Stock";
    case "out_of_stock": return "Out of Stock";
  }
}

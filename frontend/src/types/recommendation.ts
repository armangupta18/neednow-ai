export interface Product {
  id: string;
  name: string;
  price: number;
  quantity: number;
  image_url?: string;
  reason?: string;
}

export interface EcoAlternative {
  name: string;
  eco_score: number;
  carbon_saved: string;
}

export interface SupervisorResponse {
  intent: string;
  urgency_level: string;
  reasoning: string;
  products: Product[];
  eco_alternative?: EcoAlternative;
}

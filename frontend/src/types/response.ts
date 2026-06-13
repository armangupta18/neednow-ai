export interface IntentResponse {
  cart: {
    category: string;

    products: {
      id: string;
      title: string;
      price: number;
      score: number;
    }[];

    bundles: {
      id: string;
      title: string;
      price: number;
    }[];
  };

  urgency: {
    level: string;
    score: number;
    explanation: string;
  };

  reasoning: string;

  eco_alternative?: {
    alternative_product_name: string;
    carbon_saved: number;
    price_difference: number;
    sustainability_score: number;
  };
}

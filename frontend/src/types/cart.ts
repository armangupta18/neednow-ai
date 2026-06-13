export interface CartProduct {
  id: string;
  title: string;
  price: number;
  score?: number;
}

export interface Cart {
  category: string;
  products: CartProduct[];
  bundles: CartProduct[];
}

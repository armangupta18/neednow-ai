import { Product } from "@/types/recommendation";
import CartItem from "./CartItem";

interface Props {
  products: Product[];
}

export default function CartView({ products }: Props) {
  const total = products.reduce(
    (sum, item) => sum + item.price * item.quantity,
    0,
  );

  return (
    <div className="space-y-4">
      <h2 className="font-bold text-xl">Recommended Cart</h2>

      {products.map((product) => (
        <CartItem key={product.id} product={product} />
      ))}

      <div
        className="
        text-right
        font-bold
        text-xl
        "
      >
        Total: ₹{total}
      </div>
    </div>
  );
}

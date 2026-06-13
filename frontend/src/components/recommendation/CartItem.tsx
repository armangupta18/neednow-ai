import { Product } from "@/types/recommendation";

interface Props {
  product: Product;
}

export default function CartItem({ product }: Props) {
  return (
    <div
      className="
      flex
      justify-between
      items-center
      border
      rounded-lg
      p-4
      "
    >
      <div>
        <h3 className="font-semibold">{product.name}</h3>

        <p className="text-sm text-gray-500">{product.reason}</p>
      </div>

      <div className="font-bold">₹{product.price}</div>
    </div>
  );
}

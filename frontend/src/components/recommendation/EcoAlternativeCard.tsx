import { EcoAlternative } from "@/types/recommendation";

interface Props {
  alternative: EcoAlternative;
}

export default function EcoAlternativeCard({ alternative }: Props) {
  return (
    <div
      className="
      bg-green-50
      border-green-300
      border
      rounded-xl
      p-5
      "
    >
      <h2 className="font-bold text-lg">Sustainable Alternative</h2>

      <div className="mt-3">
        <p>{alternative.name}</p>

        <p>Eco Score: {alternative.eco_score}</p>

        <p>Carbon Saved: {alternative.carbon_saved}</p>
      </div>
    </div>
  );
}

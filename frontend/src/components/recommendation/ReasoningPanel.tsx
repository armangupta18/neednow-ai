interface Props {
  reasoning: string;
}

export default function ReasoningPanel({ reasoning }: Props) {
  return (
    <div
      className="
      bg-white
      rounded-xl
      shadow
      p-5
      border
      "
    >
      <h2 className="font-bold text-lg mb-3">AI Reasoning</h2>

      <p className="text-gray-700">{reasoning}</p>
    </div>
  );
}

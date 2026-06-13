interface Props {
  level: string;
}

export default function UrgencyBadge({ level }: Props) {
  const colorMap: Record<string, string> = {
    LOW: "bg-green-500",
    MEDIUM: "bg-yellow-500",
    HIGH: "bg-orange-500",
    CRITICAL: "bg-red-500",
  };

  return (
    <div
      className={`
      inline-flex
      px-4
      py-2
      rounded-full
      text-white
      font-semibold
      ${colorMap[level] || "bg-gray-500"}
      `}
    >
      {level}
    </div>
  );
}

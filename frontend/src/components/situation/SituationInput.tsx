"use client";

import { useState } from "react";

interface Props {
  onSubmit: (value: string) => Promise<void>;
}

export default function SituationInput({ onSubmit }: Props) {
  const [value, setValue] = useState("");

  const handleSubmit = async () => {
    if (!value.trim()) return;

    await onSubmit(value);
  };

  return (
    <div className="space-y-4">
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Describe your situation..."
        className="
          w-full
          border
          rounded-lg
          p-4
          min-h-[120px]
        "
      />

      <button
        onClick={handleSubmit}
        className="
          bg-black
          text-white
          px-4
          py-2
          rounded-lg
          hover:opacity-90
        "
      >
        Generate Cart
      </button>
    </div>
  );
}

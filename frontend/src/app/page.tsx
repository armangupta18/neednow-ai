"use client";

import SituationInput from "@/components/situation/SituationInput";

import { useIntent } from "@/hooks/useIntent";

export default function HomePage() {
  const { generateCart, loading, error, data } = useIntent();

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h2 className="text-4xl font-bold mb-2">Situation → Cart</h2>

      <p className="mb-8 text-muted-foreground">
        Describe your situation and let NeedNow AI build a cart.
      </p>

      <SituationInput onSubmit={generateCart} />

      {loading && <p className="mt-4">Generating...</p>}

      {error && <p className="mt-4 text-red-500">{error}</p>}

      {data && (
        <pre className="mt-8 p-4 border rounded-lg overflow-auto">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  );
}

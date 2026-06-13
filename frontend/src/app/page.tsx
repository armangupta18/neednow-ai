"use client";

import SituationInput from "@/components/situation/SituationInput";

import ResultSection from "@/components/recommendation/ResultSection";

import { useSupervisor } from "@/hooks/useSupervisor";

import { useRecommendationStore } from "@/store/useRecommendationStore";

export default function HomePage() {
  const { generateCart } = useSupervisor();

  const { result, setResult } = useRecommendationStore();

  const handleSubmit = async (situation: string) => {
    const data = await generateCart(situation);

    setResult(data);
  };

  return (
    <main className="container mx-auto py-10">
      <SituationInput onSubmit={handleSubmit} />

      {result && <ResultSection result={result} />}
    </main>
  );
}

"use client";

import UrgencyBadge from "./UrgencyBadge";
import ReasoningPanel from "./ReasoningPanel";
import CartView from "./CartView";
import EcoAlternativeCard from "./EcoAlternativeCard";

import { SupervisorResponse } from "@/types/recommendation";

interface Props {
  result: SupervisorResponse;
}

export default function ResultSection({ result }: Props) {
  return (
    <div className="space-y-6 mt-10">
      <UrgencyBadge level={result.urgency_level} />

      <ReasoningPanel reasoning={result.reasoning} />

      <CartView products={result.products} />

      {result.eco_alternative && (
        <EcoAlternativeCard alternative={result.eco_alternative} />
      )}
    </div>
  );
}

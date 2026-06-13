import { useState } from "react";

export function useSupervisor() {
  const [loading, setLoading] = useState(false);

  const generateCart = async (situation: string) => {
    try {
      setLoading(true);

      const response = await fetch("http://localhost:8000/api/v1/supervisor", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: "demo-user",
          situation,
        }),
      });

      return await response.json();
    } finally {
      setLoading(false);
    }
  };

  return {
    loading,
    generateCart,
  };
}

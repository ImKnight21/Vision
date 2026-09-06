import { useCallback, useEffect, useState } from "react";

export type Phosphor = "green" | "amber";

const STORAGE_KEY = "vision.phosphor";

function readStored(): Phosphor {
  try {
    return localStorage.getItem(STORAGE_KEY) === "amber" ? "amber" : "green";
  } catch {
    // Private windows and blocked site data throw on access, not on read.
    return "green";
  }
}

/** Which phosphor the tube is running, persisted per browser. */
export function usePhosphor(): [Phosphor, () => void] {
  const [phosphor, setPhosphor] = useState<Phosphor>(readStored);

  useEffect(() => {
    document.documentElement.dataset.phosphor = phosphor;
    try {
      localStorage.setItem(STORAGE_KEY, phosphor);
    } catch {
      // A remembered preference is a convenience; losing it is not an error.
    }
  }, [phosphor]);

  const toggle = useCallback(
    () => setPhosphor((current) => (current === "green" ? "amber" : "green")),
    [],
  );

  return [phosphor, toggle];
}

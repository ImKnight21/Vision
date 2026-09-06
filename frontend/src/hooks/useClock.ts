import { useEffect, useState } from "react";

/** UTC wall clock, ticking once a second. Markets run on UTC; so does this. */
export function useClock(): string {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(id);
  }, []);

  return now.toISOString().slice(11, 19);
}

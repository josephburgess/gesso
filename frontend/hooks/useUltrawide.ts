import { useEffect, useState } from 'react';

const isUltrawide = () => window.innerWidth / window.innerHeight >= 1.9;

export default function useUltrawide() {
  const [ultrawide, setUltrawide] = useState(isUltrawide);

  useEffect(() => {
    const update = () => setUltrawide(isUltrawide());
    window.addEventListener('resize', update);
    return () => window.removeEventListener('resize', update);
  }, []);

  return ultrawide;
}

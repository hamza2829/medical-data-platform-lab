export function chartCoordinates(values: number[], width = 360, height = 120): string {
  if (values.length === 0) return '';
  const min = Math.min(...values); const max = Math.max(...values); const span = max - min || 1;
  return values.map((value, index) => {
    const x = values.length === 1 ? width / 2 : (index / (values.length - 1)) * width;
    const y = height - 8 - ((value - min) / span) * (height - 16);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');
}

export function displayName(name: Array<{ family?: string; given?: string[]; text?: string }>): string {
  const entry = name[0];
  if (!entry) return 'Unnamed synthetic patient';
  return entry.text || [...(entry.given || []), entry.family || ''].filter(Boolean).join(' ');
}

export function trendLabel(direction: string): string {
  if (direction === 'rising') return 'Rising';
  if (direction === 'falling') return 'Falling';
  return 'Steady';
}

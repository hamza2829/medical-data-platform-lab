import { describe, expect, it } from 'vitest';
import { chartCoordinates, displayName, trendLabel } from './calculations';

describe('chartCoordinates', () => {
  it('returns an accessible chart point for a single reading', () => { expect(chartCoordinates([12])).toBe('180.0,112.0'); });
  it('scales low and high values into the chart bounds', () => { const points = chartCoordinates([0, 10]).split(' '); expect(points[0]).toBe('0.0,112.0'); expect(points[1]).toBe('360.0,8.0'); });
  it('keeps flat series in a stable horizontal line', () => { const points = chartCoordinates([4, 4, 4]).split(' '); expect(points[0].split(',')[1]).toBe(points[2].split(',')[1]); });
  it('returns an empty path for no values', () => { expect(chartCoordinates([])).toBe(''); });
  it('supports a custom chart size', () => { expect(chartCoordinates([0, 1], 100, 50)).toContain('100.0,8.0'); });
});

describe('displayName and trendLabel', () => {
  it('joins given and family names', () => { expect(displayName([{ given: ['Mina'], family: 'Solberg' }])).toBe('Mina Solberg'); });
  it('uses an explicit text name when present', () => { expect(displayName([{ text: 'p-abcdef123456', family: 'Hidden' }])).toBe('p-abcdef123456'); });
  it('provides a safe fallback when name is missing', () => { expect(displayName([])).toContain('Unnamed'); });
  it('translates trend directions for display', () => { expect(trendLabel('rising')).toBe('Rising'); expect(trendLabel('falling')).toBe('Falling'); expect(trendLabel('steady')).toBe('Steady'); });
});

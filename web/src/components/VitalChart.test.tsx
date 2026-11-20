import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { VitalChart } from './VitalChart';
import type { Trend } from '../types';

const trend: Trend = { code: '8867-4', name: 'Heart rate', unit: 'beats/min', count: 3, change: 7, direction: 'rising', points: [{ value: 70, effectiveDateTime: '2026-01-01T10:00:00Z' }, { value: 73, effectiveDateTime: '2026-01-01T10:05:00Z' }, { value: 77, effectiveDateTime: '2026-01-01T10:10:00Z' }] };
describe('VitalChart', () => {
  it('exposes its chart as an image with a useful accessible description', () => { render(<VitalChart trend={trend} />); expect(screen.getByRole('img', { name: /Heart rate trend: Rising, latest 77 beats\/min/ })).toBeInTheDocument(); });
  it('shows the latest value and trend label', () => { render(<VitalChart trend={trend} />); expect(screen.getByText('77')).toBeInTheDocument(); expect(screen.getByText(/Rising/)).toBeInTheDocument(); });
  it('draws a line and point marks for the readings', () => { const { container } = render(<VitalChart trend={trend} />); expect(container.querySelector('polyline')).toHaveAttribute('points'); expect(container.querySelectorAll('circle')).toHaveLength(3); });
  it('handles a metric with no data', () => { const empty = { ...trend, count: 0, points: [], change: 0 }; render(<VitalChart trend={empty} />); expect(screen.getByText('—')).toBeInTheDocument(); });
});

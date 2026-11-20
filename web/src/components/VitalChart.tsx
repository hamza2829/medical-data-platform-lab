import { chartCoordinates, trendLabel } from '../calculations';
import type { Trend } from '../types';

export function VitalChart({ trend }: { trend: Trend }) {
  const values = trend.points.map(point => point.value);
  const last = values[values.length - 1];
  const label = `${trend.name} trend: ${trendLabel(trend.direction)}, latest ${last ?? 'no'} ${trend.unit || ''}`.trim();
  return <article className="vital-card">
    <div className="vital-card-head"><div><p className="micro-label">VITAL SIGN</p><h3>{trend.name}</h3></div><span className={`trend-chip trend-${trend.direction}`}><span aria-hidden="true">{trend.direction === 'rising' ? '↗' : trend.direction === 'falling' ? '↘' : '→'}</span> {trendLabel(trend.direction)}</span></div>
    <div className="vital-reading"><strong>{last ?? '—'}</strong><span>{trend.unit}</span><small>{trend.count} readings</small></div>
    <svg className="vital-chart" viewBox="0 0 360 120" role="img" aria-label={label} preserveAspectRatio="none">
      <line x1="0" y1="112" x2="360" y2="112" stroke="#e7edf0" strokeWidth="1" />
      <polyline points={chartCoordinates(values)} fill="none" stroke="#397fbe" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
      {values.map((value, index) => { const points = chartCoordinates(values).split(' '); const [cx, cy] = (points[index] || '0,0').split(','); return <circle key={`${index}-${value}`} cx={cx} cy={cy} r="3" fill="#fff" stroke="#397fbe" strokeWidth="2" vectorEffect="non-scaling-stroke" />; })}
    </svg>
    <div className="vital-card-foot"><span>Earlier</span><span>Latest</span><span className="change-value">{trend.change > 0 ? '+' : ''}{trend.change} {trend.unit}</span></div>
  </article>;
}

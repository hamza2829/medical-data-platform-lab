import { useMemo, useState } from 'react';
import { displayName } from '../calculations';
import type { Patient } from '../types';

type Props = { patients: Patient[]; selectedId?: string; onSelect: (patient: Patient) => void };
export function PatientList({ patients, selectedId, onSelect }: Props) {
  const [query, setQuery] = useState('');
  const filtered = useMemo(() => patients.filter(patient => displayName(patient.name).toLowerCase().includes(query.toLowerCase())), [patients, query]);
  return <section className="patient-list" aria-labelledby="patients-heading">
    <div className="panel-title-row"><div><p className="kicker">CONNECTED RECORDS</p><h2 id="patients-heading">Patients <span className="result-count">{patients.length}</span></h2></div><span className="online-indicator"><i/> All systems ready</span></div>
    <label className="search-label" htmlFor="patient-search">Search synthetic patients</label><div className="search-field"><span aria-hidden="true">⌕</span><input id="patient-search" value={query} onChange={event => setQuery(event.target.value)} placeholder="Name or record ID" /></div>
    <ul className="patient-items">
      {filtered.map((patient, index) => <li key={patient.id}><button type="button" className={`patient-row ${selectedId === patient.id ? 'selected' : ''}`} aria-current={selectedId === patient.id ? 'page' : undefined} onClick={() => onSelect(patient)}>
        <span className={`patient-avatar avatar-${index % 4}`} aria-hidden="true">{displayName(patient.name).split(' ').map(part => part[0]).slice(0, 2).join('')}</span>
        <span className="patient-row-copy"><strong>{displayName(patient.name)}</strong><span>Demo record · {patient.gender || 'unknown'}</span></span>
        <span className="row-chevron" aria-hidden="true">›</span>
      </button></li>)}
      {!filtered.length && <li className="no-results">No matching synthetic patients.</li>}
    </ul>
    <p className="list-footnote"><span aria-hidden="true">◈</span> De-identified training data only</p>
  </section>;
}

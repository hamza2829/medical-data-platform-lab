import { useEffect, useMemo, useState } from 'react';
import { api, getAnalysis, getPatient, getPatients, login } from './api';
import { displayName } from './calculations';
import { LoginForm } from './components/LoginForm';
import { PatientList } from './components/PatientList';
import { TeamAdmin } from './components/TeamAdmin';
import { VitalChart } from './components/VitalChart';
import type { Analysis, Patient, User } from './types';

type Page = 'patients' | 'team';
export default function App() {
  const [token, setToken] = useState(''); const [user, setUser] = useState<User | null>(null);
  const [patients, setPatients] = useState<Patient[]>([]); const [selectedId, setSelectedId] = useState('');
  const [patient, setPatient] = useState<Patient | null>(null); const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [page, setPage] = useState<Page>('patients'); const [error, setError] = useState(''); const [loading, setLoading] = useState(false);
  async function signIn(username: string, password: string) { const session = await login(username, password); setToken(session.token); setUser(session.user); setPage('patients'); }
  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    setLoading(true); setError('');
    getPatients(token).then(result => {
      if (!cancelled) { const rows = result.entry.map(item => item.resource); setPatients(rows); setSelectedId(current => current || rows[0]?.id || ''); }
    }).catch(reason => { if (!cancelled) setError(reason instanceof Error ? reason.message : 'Patients could not be loaded.'); }).finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [token]);
  useEffect(() => {
    if (!token || !selectedId) { setPatient(null); setAnalysis(null); return; }
    let cancelled = false;
    Promise.all([getPatient(token, selectedId), getAnalysis(token, selectedId)]).then(([record, result]) => {
      if (!cancelled) { setPatient(record); setAnalysis(result); }
    }).catch(reason => { if (!cancelled) setError(reason instanceof Error ? reason.message : 'Patient details could not be loaded.'); });
    return () => { cancelled = true; };
  }, [token, selectedId]);
  const alerts = useMemo(() => analysis?.alerts || [], [analysis]);
  async function signOut() { try { if (token) await api<void>('/auth/logout/', token, { method: 'POST' }); } finally { setToken(''); setUser(null); setPatients([]); setPatient(null); setAnalysis(null); } }
  async function exportPseudonymized() {
    try { const body = await api<unknown>('/exports/pseudonymized/', token); const href = URL.createObjectURL(new Blob([JSON.stringify(body, null, 2)], { type: 'application/json' })); const link = document.createElement('a'); link.href = href; link.download = 'pseudonymized-fhir-export.json'; link.click(); URL.revokeObjectURL(href); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Export could not be prepared.'); }
  }
  async function exportGdpr() {
    if (!patient) return;
    try { const body = await api<unknown>(`/patients/${patient.id}/gdpr-export/`, token); const href = URL.createObjectURL(new Blob([JSON.stringify(body, null, 2)], { type: 'application/json' })); const link = document.createElement('a'); link.href = href; link.download = `gdpr-export-${patient.id}.json`; link.click(); URL.revokeObjectURL(href); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'GDPR export failed.'); }
  }
  async function deletePatient() {
    if (!patient || !window.confirm(`Permanently delete synthetic record ${patient.id} and linked observations?`)) return;
    try { await api<void>(`/patients/${patient.id}/gdpr-delete/`, token, { method: 'DELETE' }); setPatients(rows => rows.filter(row => row.id !== patient.id)); setSelectedId(''); setPatient(null); setAnalysis(null); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Delete failed.'); }
  }
  if (!user) return <LoginForm onLogin={signIn} />;
  const canWrite = user.role === 'admin' || user.role === 'clinician';
  return <div className="app-frame">
    <header className="top-header"><a className="brand-lockup" href="#patients" aria-label="Northstar Medical Data Lab home"><span className="brand-glyph" aria-hidden="true">✳</span><span>northstar<span className="brand-period">.</span></span><span className="brand-subtitle">MEDICAL DATA LAB</span></a>
      <nav className="primary-nav" aria-label="Primary navigation"><button className={page === 'patients' ? 'nav-active' : ''} onClick={() => setPage('patients')}>Patients</button>{user.role === 'admin' && <button className={page === 'team' ? 'nav-active' : ''} onClick={() => setPage('team')}>Team access</button>}</nav>
      <div className="top-user"><span className="environment-tag"><i/> Synthetic environment</span><span className="top-user-name">{user.username}<small>{user.role}</small></span><button className="signout-button" onClick={signOut}>Sign out</button></div>
    </header>
    <main className="main-area">
      <div className="privacy-banner" role="note"><span className="privacy-symbol" aria-hidden="true">◇</span><span><strong>Training workspace.</strong> Every patient and reading is synthetic. Never enter real health information.</span><span className="fhir-tag">FHIR R4 · schema 1.0.0</span></div>
      {error && <div className="error-banner" role="alert">{error}<button onClick={() => setError('')} aria-label="Dismiss error">×</button></div>}
      {page === 'team' && user.role === 'admin' ? <TeamAdmin token={token} currentUserId={user.id} /> : <div className="patient-workspace">
        <aside className="patient-sidebar"><PatientList patients={patients} selectedId={selectedId} onSelect={row => { setSelectedId(row.id); setPage('patients'); }} /></aside>
        <section className="patient-content" aria-labelledby="patient-title">
          <div className="patient-page-heading"><div><p className="kicker">PATIENT OVERVIEW <span className="slash">/</span> SENSOR FEED</p><h1 id="patient-title">{patient ? displayName(patient.name) : loading ? 'Loading records…' : 'Choose a patient'}</h1><p className="patient-subtitle">{patient ? <>Synthetic record <code>{patient.id}</code> <span aria-hidden="true">·</span> Updated {patient.meta?.lastUpdated ? new Date(patient.meta.lastUpdated).toLocaleString() : 'just now'}</> : 'Select a record to inspect recent observations and trends.'}</p></div>
            {patient && <div className="patient-actions">{(user.role === 'researcher' || user.role === 'admin') && <button className="secondary-button" onClick={exportPseudonymized}>Export pseudonymized</button>}{canWrite && <button className="secondary-button" onClick={exportGdpr}>GDPR export</button>}{user.role === 'admin' && <button className="delete-button" onClick={deletePatient}>Delete data</button>}</div>}
          </div>
          {loading && <p className="loading-message" role="status">Loading synthetic records…</p>}
          {!loading && patient && analysis && <>
            <div className="patient-summary-grid"><article className="summary-tile"><span>OBSERVATIONS</span><strong>{analysis.observation_count}</strong><small>FHIR records</small></article><article className="summary-tile"><span>PROFILE GENDER</span><strong className="summary-word">{patient.gender || 'unknown'}</strong><small>FHIR Patient</small></article><article className="summary-tile"><span>RESOURCE VERSION</span><strong>v{patient.meta?.versionId || '1'}</strong><small>Schema {patient.meta?.versionId ? '1.0.0' : '1.0.0'}</small></article><article className="summary-tile summary-status"><span>DEVICE STATUS</span><strong><i/> Connected</strong><small>MQTT ingest ready</small></article></div>
            {alerts.length > 0 && <section className="alerts-panel" aria-labelledby="alerts-title"><div className="alerts-heading"><span className="alert-icon" aria-hidden="true">!</span><div><p className="kicker">RULE BASED REVIEW</p><h2 id="alerts-title">Signals to review <span>{alerts.length}</span></h2></div><span className="demo-note">Demo thresholds · not medical advice</span></div><ul>{alerts.map((alert, index) => <li key={`${alert.code}-${index}`}><span className="alert-line"/><div><strong>{alert.label}</strong><p>{alert.message} Latest synthetic value: {alert.value}.</p></div><span className={`severity severity-${alert.severity}`}>{alert.severity}</span></li>)}</ul></section>}
            <section className="trend-section" aria-labelledby="trends-title"><div className="trend-section-title"><div><p className="kicker">RECENT SENSOR READINGS</p><h2 id="trends-title">Vital sign trends</h2></div><span className="trend-count">{analysis.trends.length} measures <i/> Live demo feed</span></div><div className="trend-grid">{analysis.trends.map(trend => <VitalChart key={trend.code} trend={trend} />)}{!analysis.trends.length && <p>No observations available for this synthetic patient.</p>}</div></section>
            <div className="version-note"><span aria-hidden="true">◷</span> Each resource write creates a version snapshot. Read and write access is logged without storing health values in the audit trail.</div>
          </>}
          {!loading && !patient && <div className="empty-selection">Select a synthetic patient from the list to review observations.</div>}
        </section>
      </div>}
      {page === 'patients' && user.role !== 'admin' && <p className="role-hint">Signed in with <strong>{user.role}</strong> access. Patient records and exports are limited by this role.</p>}
    </main>
  </div>;
}

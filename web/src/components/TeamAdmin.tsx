import { FormEvent, useEffect, useState } from 'react';
import { api, getUsers } from '../api';
import type { Role, User } from '../types';

export function TeamAdmin({ token, currentUserId }: { token: string; currentUserId: number }) {
  const [users, setUsers] = useState<User[]>([]); const [error, setError] = useState(''); const [saved, setSaved] = useState('');
  const [username, setUsername] = useState(''); const [email, setEmail] = useState(''); const [password, setPassword] = useState(''); const [role, setRole] = useState<Role>('clinician');
  async function refresh() { try { setUsers(await getUsers(token)); } catch (reason) { setError(reason instanceof Error ? reason.message : 'Users could not be loaded.'); } }
  useEffect(() => { void refresh(); }, [token]);
  async function createUser(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(''); setSaved('');
    try { await api<User>('/users/', token, { method: 'POST', body: JSON.stringify({ username, email, password, role }) }); setUsername(''); setEmail(''); setPassword(''); setSaved('Team member added.'); await refresh(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'User could not be created.'); }
  }
  async function updateUser(user: User, patch: Partial<Pick<User, 'role' | 'is_active'>>) {
    try { const updated = await api<User>(`/users/${user.id}/`, token, { method: 'PATCH', body: JSON.stringify(patch) }); setUsers(rows => rows.map(row => row.id === user.id ? updated : row)); setSaved(`${user.username} updated.`); setError(''); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'User could not be updated.'); }
  }
  async function removeUser(user: User) {
    if (!window.confirm(`Remove the synthetic user ${user.username}?`)) return;
    try { await api<void>(`/users/${user.id}/`, token, { method: 'DELETE' }); setUsers(rows => rows.filter(row => row.id !== user.id)); setSaved(`${user.username} removed.`); setError(''); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'User could not be removed.'); }
  }
  return <section className="team-screen" aria-labelledby="team-title">
    <div className="screen-heading"><div><p className="kicker">ACCESS & PERMISSIONS</p><h1 id="team-title">Team members</h1><p>People and roles in this synthetic workspace.</p></div><span className="schema-pill">ROLE BASED ACCESS</span></div>
    {error && <p role="alert" className="inline-error">{error}</p>}{saved && <p role="status" className="inline-success">{saved}</p>}
    <div className="team-layout"><div className="panel team-table-panel"><h2>Workspace users <span>{users.length}</span></h2><div className="table-scroll"><table><caption className="sr-only">Synthetic users and access roles</caption><thead><tr><th scope="col">User</th><th scope="col">Role</th><th scope="col">Status</th><th scope="col">Manage</th></tr></thead><tbody>{users.map(item => <tr key={item.id}><td><strong>{item.username}</strong><span>{item.email}</span></td><td><span className={`role-pill role-${item.role}`}>{item.role}</span></td><td><span className="status-dot"><i/>{item.is_active ? 'Active' : 'Inactive'}</span></td><td><div className="user-actions">{item.id !== currentUserId && <><label className="sr-only" htmlFor={`role-${item.id}`}>Role for {item.username}</label><select id={`role-${item.id}`} value={item.role} onChange={event => void updateUser(item, { role: event.target.value as Role })}><option value="admin">Admin</option><option value="clinician">Clinician</option><option value="researcher">Researcher</option></select><button type="button" onClick={() => void updateUser(item, { is_active: !item.is_active })}>{item.is_active ? 'Deactivate' : 'Activate'}</button><button type="button" className="remove-user" onClick={() => void removeUser(item)}>Remove</button></>}</div></td></tr>)}</tbody></table></div></div>
      <form className="panel add-user-form" onSubmit={createUser}>
        <p className="kicker">NEW ACCESS</p><h2>Add a team member</h2><p className="form-intro">Credentials are stored as salted password hashes.</p>
        <label htmlFor="new-username">Username</label><input id="new-username" autoComplete="off" required value={username} onChange={e => setUsername(e.target.value)} />
        <label htmlFor="new-email">Email</label><input id="new-email" type="email" required value={email} onChange={e => setEmail(e.target.value)} />
        <label htmlFor="new-password">Temporary password</label><input id="new-password" type="password" minLength={12} autoComplete="new-password" required value={password} onChange={e => setPassword(e.target.value)} />
        <label htmlFor="new-role">Role</label><select id="new-role" value={role} onChange={e => setRole(e.target.value as Role)}><option value="clinician">Clinician · read and write</option><option value="researcher">Researcher · read and export</option><option value="admin">Admin · manage users</option></select>
        <button className="primary-button" type="submit">Create user <span aria-hidden="true">→</span></button>
      </form></div>
    <p className="privacy-note"><strong>Access note</strong> Demo tokens do not expire automatically. Revoke tokens when a demo user is removed. Enforce HTTPS and a short-lived token policy before any real deployment.</p>
  </section>;
}

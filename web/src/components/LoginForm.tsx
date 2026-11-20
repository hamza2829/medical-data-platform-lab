import { FormEvent, useState } from 'react';

type Props = { onLogin: (username: string, password: string) => Promise<void> };
export function LoginForm({ onLogin }: Props) {
  const [username, setUsername] = useState('demo-admin'); const [password, setPassword] = useState('DemoAdmin2026!');
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError('');
    try { await onLogin(username, password); } catch (reason) { setError(reason instanceof Error ? reason.message : 'Sign in failed.'); }
    finally { setBusy(false); }
  }
  return <main className="login-page"><section className="login-card" aria-labelledby="login-title">
    <div className="brand-lockup"><span className="brand-glyph" aria-hidden="true">✳</span><span>northstar<span className="brand-period">.</span></span></div>
    <p className="kicker">MEDICAL DATA LAB</p><h1 id="login-title">A clearer view<br />of every signal.</h1><p className="login-copy">A synthetic data workspace for exploring connected care.</p>
    <form onSubmit={submit}>
      <label htmlFor="username">Username</label><input id="username" name="username" autoComplete="username" required value={username} onChange={(event) => setUsername(event.target.value)} />
      <label htmlFor="password">Password</label><input id="password" name="password" type="password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} />
      {error && <p className="form-error" role="alert">{error}</p>}
      <button className="primary-button login-button" type="submit" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'} <span aria-hidden="true">→</span></button>
    </form>
    <p className="login-footnote">Demo credentials are prefilled · Synthetic records only</p>
  </section><aside className="login-visual" aria-hidden="true"><div className="orbit orbit-one"/><div className="orbit orbit-two"/><div className="orbit orbit-three"/><div className="visual-center">N</div><div className="visual-label">SIGNAL / PATTERN / CARE</div></aside></main>;
}

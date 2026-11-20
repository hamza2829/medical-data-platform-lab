import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { LoginForm } from './LoginForm';

describe('LoginForm', () => {
  it('labels the username and password inputs', () => { render(<LoginForm onLogin={vi.fn()} />); expect(screen.getByLabelText('Username')).toBeInTheDocument(); expect(screen.getByLabelText('Password')).toHaveAttribute('type', 'password'); });
  it('prefills the seeded synthetic administrator account', () => { render(<LoginForm onLogin={vi.fn()} />); expect(screen.getByLabelText('Username')).toHaveValue('demo-admin'); expect(screen.getByLabelText('Password')).toHaveValue('DemoAdmin2026!'); });
  it('submits credentials and announces completion', async () => { const onLogin = vi.fn().mockResolvedValue(undefined); render(<LoginForm onLogin={onLogin} />); await userEvent.click(screen.getByRole('button', { name: /sign in/i })); await waitFor(() => expect(onLogin).toHaveBeenCalledWith('demo-admin', 'DemoAdmin2026!')); });
  it('shows an accessible error when authentication fails', async () => { const onLogin = vi.fn().mockRejectedValue(new Error('Invalid username or password.')); render(<LoginForm onLogin={onLogin} />); fireEvent.submit(screen.getByRole('button', { name: /sign in/i }).closest('form')!); expect(await screen.findByRole('alert')).toHaveTextContent('Invalid username or password.'); });
});

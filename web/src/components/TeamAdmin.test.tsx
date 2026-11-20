import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { TeamAdmin } from './TeamAdmin';
import type { User } from '../types';

const member: User = { id: 2, username: 'demo-clinician', email: 'demo-clinician@example.test', role: 'clinician', is_active: true };
const reply = (body: unknown, status = 200) => ({ ok: status < 400, status, json: async () => body });
afterEach(() => vi.unstubAllGlobals());

describe('TeamAdmin', () => {
  it('lists the workspace user and exposes an accessible role selector', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(reply([member])));
    render(<TeamAdmin token="fake-token" currentUserId={1} />);
    expect(await screen.findByText('demo-clinician@example.test')).toBeInTheDocument();
    expect(screen.getByLabelText('Role for demo-clinician')).toHaveValue('clinician');
  });
  it('sends role changes to the admin API', async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(reply([member])).mockResolvedValueOnce(reply({ ...member, role: 'researcher' }));
    vi.stubGlobal('fetch', fetchMock);
    render(<TeamAdmin token="fake-token" currentUserId={1} />);
    await screen.findByText('demo-clinician@example.test');
    await userEvent.selectOptions(screen.getByLabelText('Role for demo-clinician'), 'researcher');
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(fetchMock.mock.calls[1][0]).toContain('/users/2/');
    expect(JSON.parse(fetchMock.mock.calls[1][1].body)).toEqual({ role: 'researcher' });
    expect(await screen.findByText('demo-clinician updated.')).toBeInTheDocument();
  });
  it('prevents the active administrator from being managed as another user', async () => {
    const admin: User = { id: 1, username: 'demo-admin', email: 'demo-admin@example.test', role: 'admin', is_active: true };
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(reply([admin])));
    render(<TeamAdmin token="fake-token" currentUserId={1} />);
    await screen.findByText('demo-admin@example.test');
    expect(screen.queryByLabelText('Role for demo-admin')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Remove' })).not.toBeInTheDocument();
  });
  it('creates a user with a selected role', async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(reply([])).mockResolvedValueOnce(reply({ ...member, id: 3, username: 'new-researcher', role: 'researcher' }, 201)).mockResolvedValueOnce(reply([{ ...member, id: 3, username: 'new-researcher', role: 'researcher' }]));
    vi.stubGlobal('fetch', fetchMock);
    render(<TeamAdmin token="fake-token" currentUserId={1} />);
    await userEvent.type(screen.getByLabelText('Username'), 'new-researcher');
    await userEvent.type(screen.getByLabelText('Email'), 'new@example.test');
    await userEvent.type(screen.getByLabelText('Temporary password'), 'ResearchAssistant2026!');
    await userEvent.selectOptions(screen.getByLabelText('Role'), 'researcher');
    fireEvent.submit(screen.getByRole('button', { name: /Create user/ }).closest('form')!);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    expect(JSON.parse(fetchMock.mock.calls[1][1].body).role).toBe('researcher');
    expect(await screen.findByText('Team member added.')).toBeInTheDocument();
  });
});

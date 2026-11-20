import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { PatientList } from './PatientList';
import type { Patient } from '../types';

const patients: Patient[] = [
  { resourceType: 'Patient', id: 'p-a', name: [{ given: ['Mina'], family: 'Solberg' }], gender: 'female' },
  { resourceType: 'Patient', id: 'p-b', name: [{ given: ['Theo'], family: 'Calder' }], gender: 'male' },
];
describe('PatientList', () => {
  it('renders a labelled search and synthetic patient rows', () => { render(<PatientList patients={patients} onSelect={vi.fn()} />); expect(screen.getByLabelText('Search synthetic patients')).toBeInTheDocument(); expect(screen.getByRole('button', { name: /Mina Solberg/ })).toBeInTheDocument(); });
  it('filters records by name', () => { render(<PatientList patients={patients} onSelect={vi.fn()} />); fireEvent.change(screen.getByLabelText('Search synthetic patients'), { target: { value: 'theo' } }); expect(screen.getByText('Theo Calder')).toBeInTheDocument(); expect(screen.queryByText('Mina Solberg')).not.toBeInTheDocument(); });
  it('announces an empty search result', () => { render(<PatientList patients={patients} onSelect={vi.fn()} />); fireEvent.change(screen.getByLabelText('Search synthetic patients'), { target: { value: 'unknown' } }); expect(screen.getByText('No matching synthetic patients.')).toBeInTheDocument(); });
  it('marks the selected patient and emits selection', () => { const onSelect = vi.fn(); render(<PatientList patients={patients} selectedId="p-a" onSelect={onSelect} />); expect(screen.getByRole('button', { name: /Mina Solberg/ })).toHaveAttribute('aria-current', 'page'); fireEvent.click(screen.getByRole('button', { name: /Theo Calder/ })); expect(onSelect).toHaveBeenCalledWith(patients[1]); });
});

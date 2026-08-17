import React from 'react';
import { render, screen } from '@testing-library/react';
import Sources from './Sources';

describe('Sources', () => {
  it('renders every source as an external link with an http(s) URL', () => {
    render(<Sources />);

    const links = screen.getAllByRole('link');
    expect(links.length).toBeGreaterThan(0);
    for (const link of links) {
      expect(link.getAttribute('href')).toMatch(/^https?:\/\//);
      expect(link).toHaveAttribute('target', '_blank');
    }
  });

  it('renders at least one automated and one non-automated source', () => {
    render(<Sources />);

    expect(screen.getAllByText('Автоматизировано').length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Только вручную|Заблокировано|Не реализовано|Решено не делать|Не подходит/).length).toBeGreaterThan(0);
  });

  it('has no duplicate source names', () => {
    render(<Sources />);

    const links = screen.getAllByRole('link').map((l) => l.textContent);
    expect(new Set(links).size).toBe(links.length);
  });
});

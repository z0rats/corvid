import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import CountryFlag from './CountryFlag';

describe('CountryFlag', () => {
  it('maps a two-letter code to its regional-indicator pair, case-insensitively', () => {
    const { rerender } = render(<CountryFlag countryCode="de" />);
    expect(screen.getByRole('img', { name: 'DE' })).toHaveTextContent('🇩🇪');
    rerender(<CountryFlag countryCode="US" />);
    expect(screen.getByRole('img', { name: 'US' })).toHaveTextContent('🇺🇸');
  });

  it('labels the flag with the title when given', () => {
    render(<CountryFlag countryCode="fr" title="France" />);
    expect(screen.getByRole('img', { name: 'France' })).toHaveTextContent('🇫🇷');
  });

  it.each([undefined, null, '', 'USA', 'U1', '??', 42])('renders nothing for %p', (code) => {
    const { container } = render(<CountryFlag countryCode={code} />);
    expect(container).toBeEmptyDOMElement();
  });
});

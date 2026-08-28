import React from 'react';
import { render, screen } from '@testing-library/react';
import CrowdSecCountriesSection from './CrowdSecCountriesSection';

describe('CrowdSecCountriesSection', () => {
  it('renders nothing when there are no target countries', () => {
    const { container } = render(<CrowdSecCountriesSection targetCountries={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('renders nothing for an empty target countries object', () => {
    const { container } = render(<CrowdSecCountriesSection targetCountries={{}} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('renders the section title when target countries are present', () => {
    render(<CrowdSecCountriesSection targetCountries={{ US: 10, FR: 3 }} />);
    expect(screen.getByText('Target Countries by Report Count')).toBeInTheDocument();
  });
});

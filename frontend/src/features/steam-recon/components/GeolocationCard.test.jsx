import { render, screen } from '@testing-library/react';
import GeolocationCard from './GeolocationCard';

const HYPOTHESIS = {
  confidence: 'high',
  num_voters: 8,
  coverage: 0.75,
  countries: [{ code: 'US', name: 'United States', weight: 10, share: 0.8 }],
  states: [{ code: 'WA', name: 'Washington', weight: 8, share: 0.8 }],
  cities: [{ code: '1234', name: 'Bellevue', weight: 8, share: 0.8 }],
  self_declared: { country_code: 'US', country: 'United States', state: 'Washington', city: 'Bellevue' },
};

describe('GeolocationCard', () => {
  it('shows an empty-hypothesis message when there are no country candidates', () => {
    render(<GeolocationCard geolocation={{ ...HYPOTHESIS, countries: [], confidence: 'low' }} />);
    expect(screen.getByText(/not enough data/i)).toBeInTheDocument();
  });

  it('renders the confidence chip and ranked country/state/city candidates', () => {
    render(<GeolocationCard geolocation={HYPOTHESIS} />);

    expect(screen.getByText(/high confidence/i)).toBeInTheDocument();
    expect(screen.getByText('United States')).toBeInTheDocument();
    expect(screen.getByText('Washington')).toBeInTheDocument();
    expect(screen.getByText('Bellevue')).toBeInTheDocument();
    expect(screen.getAllByText('80%').length).toBeGreaterThan(0);
  });

  it('shows the voter count and coverage percentage', () => {
    render(<GeolocationCard geolocation={HYPOTHESIS} />);
    expect(screen.getByText(/8 connected friends voted, 75% had a usable location/i)).toBeInTheDocument();
  });

  it('shows the self-declared location for comparison when present', () => {
    render(<GeolocationCard geolocation={HYPOTHESIS} />);
    expect(screen.getByText(/target's own profile location/i)).toBeInTheDocument();
    expect(screen.getByText(/Bellevue, Washington, United States/)).toBeInTheDocument();
  });

  it('omits the self-declared line when the target has none', () => {
    render(<GeolocationCard geolocation={{ ...HYPOTHESIS, self_declared: null }} />);
    expect(screen.queryByText(/target's own profile location/i)).not.toBeInTheDocument();
  });

  it('falls back to the raw code when a candidate has no resolved name', () => {
    render(
      <GeolocationCard
        geolocation={{ ...HYPOTHESIS, countries: [{ code: 'ZZ', name: null, weight: 1, share: 1 }] }}
      />,
    );
    expect(screen.getByText('ZZ')).toBeInTheDocument();
  });
});

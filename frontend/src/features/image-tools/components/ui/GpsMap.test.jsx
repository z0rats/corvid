import React, { createElement } from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { createStore, Provider } from 'jotai';
import GpsMap from './GpsMap';
import { apiKeysState } from '../../../../core/state/atoms';
import { streetViewApi } from '../../services/api/streetViewApi';

vi.mock('../../services/api/streetViewApi');

const SAMPLE_GPS = {
  latitude: 40.446194,
  longitude: -79.948778,
  altitude: null,
  map_url: 'https://www.google.com/maps?q=40.446194,-79.948778',
};

function renderWithApiKeys(gps, apiKeys = {}) {
  const store = createStore();
  store.set(apiKeysState, apiKeys);
  return render(createElement(Provider, { store }, <GpsMap gps={gps} />));
}

describe('GpsMap', () => {
  it('shows a fallback message when no GPS data is present', () => {
    render(<GpsMap gps={null} />);

    expect(screen.getByText(/no gps data found/i)).toBeInTheDocument();
  });

  it('renders coordinates, altitude, and a map link when GPS data is present', () => {
    const gps = {
      latitude: 40.446194,
      longitude: -79.948778,
      altitude: 100,
      map_url: 'https://www.google.com/maps?q=40.446194,-79.948778',
    };

    render(<GpsMap gps={gps} />);

    expect(screen.getByText(/40\.446194/)).toBeInTheDocument();
    expect(screen.getByText(/-79\.948778/)).toBeInTheDocument();
    expect(screen.getByText(/100\.0 m/)).toBeInTheDocument();

    const link = screen.getByRole('link', { name: /view on map/i });
    expect(link).toHaveAttribute('href', gps.map_url);
    expect(link).toHaveAttribute('target', '_blank');
  });

  it('embeds an OpenStreetMap iframe centered on the coordinates', () => {
    const gps = {
      latitude: 40.446194,
      longitude: -79.948778,
      altitude: null,
      map_url: 'https://www.google.com/maps?q=40.446194,-79.948778',
    };

    render(<GpsMap gps={gps} />);

    const iframe = screen.getByTitle(/map showing the photo's gps position/i);
    expect(iframe.tagName).toBe('IFRAME');
    expect(iframe).toHaveAttribute('src', expect.stringContaining('openstreetmap.org/export/embed.html'));
    expect(iframe).toHaveAttribute('src', expect.stringContaining('marker=40.446194,-79.948778'));
  });

  it('shows the reverse-geocoded address when present', () => {
    const gps = {
      latitude: 40.446194,
      longitude: -79.948778,
      altitude: null,
      address: '123 Fake Street, Pittsburgh, PA',
      map_url: 'https://www.google.com/maps?q=40.446194,-79.948778',
    };

    render(<GpsMap gps={gps} />);

    expect(screen.getByText('123 Fake Street, Pittsburgh, PA')).toBeInTheDocument();
  });

  it('renders external geo tool links built from the coordinates', () => {
    const gps = {
      latitude: 40.446194,
      longitude: -79.948778,
      altitude: null,
      map_url: 'https://www.google.com/maps?q=40.446194,-79.948778',
    };

    render(<GpsMap gps={gps} />);

    const shadowMapLink = screen.getByRole('link', { name: /shadowmap/i });
    expect(shadowMapLink).toHaveAttribute(
      'href',
      'https://app.shadowmap.org/?lat=40.446194&lng=-79.948778&zoom=16'
    );

    const mapCheckingLink = screen.getByRole('link', { name: /mapchecking/i });
    expect(mapCheckingLink).toHaveAttribute('href', 'https://www.mapchecking.com/');
  });

  it('does not render Street View when no Google Maps key is configured', () => {
    renderWithApiKeys(SAMPLE_GPS, {});

    expect(screen.queryByText('Street View')).not.toBeInTheDocument();
    expect(streetViewApi.getKey).not.toHaveBeenCalled();
  });

  it('renders an embedded Street View panorama when a Google Maps key is configured', async () => {
    streetViewApi.getKey.mockResolvedValue({ key: 'test-maps-key' });

    renderWithApiKeys(SAMPLE_GPS, { google_maps: true });

    const iframe = await waitFor(() => screen.getByTitle('Street View'));
    expect(iframe.tagName).toBe('IFRAME');
    expect(iframe).toHaveAttribute('src', expect.stringContaining('key=test-maps-key'));
    expect(iframe).toHaveAttribute('src', expect.stringContaining('location=40.446194%2C-79.948778'));
  });

  it('omits the altitude suffix when altitude is not provided', () => {
    const gps = {
      latitude: 1.234567,
      longitude: 2.345678,
      altitude: null,
      map_url: 'https://www.google.com/maps?q=1.234567,2.345678',
    };

    render(<GpsMap gps={gps} />);

    expect(screen.queryByText(/alt\./)).not.toBeInTheDocument();
  });
});

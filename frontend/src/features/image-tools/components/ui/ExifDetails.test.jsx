import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ExifDetails from './ExifDetails';

describe('ExifDetails', () => {
  it('shows a fallback message when there is no EXIF data', () => {
    render(<ExifDetails exif={{}} />);

    expect(screen.getByText(/no exif data found/i)).toBeInTheDocument();
  });

  it('groups tags into collapsible sections by category', async () => {
    const exif = {
      'Image Software': 'TestSoftware 1.0',
      'GPS GPSLatitude': '[40, 26, 46.3]',
    };

    render(<ExifDetails exif={exif} />);

    expect(screen.getByText('Image')).toBeInTheDocument();
    expect(screen.getByText('GPS')).toBeInTheDocument();

    const user = userEvent.setup();
    await user.click(screen.getByText('Image'));

    expect(screen.getByText('Software')).toBeInTheDocument();
    expect(screen.getByText('TestSoftware 1.0')).toBeInTheDocument();
  });
});

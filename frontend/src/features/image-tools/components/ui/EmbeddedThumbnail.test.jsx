import React from 'react';
import { render, screen } from '@testing-library/react';
import EmbeddedThumbnail from './EmbeddedThumbnail';

describe('EmbeddedThumbnail', () => {
  it('renders nothing when there is no thumbnail', () => {
    const { container } = render(<EmbeddedThumbnail hasThumbnail={false} thumbnailBase64={null} />);

    expect(container).toBeEmptyDOMElement();
  });

  it('renders the thumbnail image when present', () => {
    render(<EmbeddedThumbnail hasThumbnail={true} thumbnailBase64="data:image/jpeg;base64,abc123" />);

    const img = screen.getByRole('img');
    expect(img).toHaveAttribute('src', 'data:image/jpeg;base64,abc123');
    expect(screen.getByText('Embedded thumbnail')).toBeInTheDocument();
  });
});

import React from 'react';
import { render, screen } from '@testing-library/react';
import ReverseSearchLinks from './ReverseSearchLinks';
import { REVERSE_SEARCH_ENGINES } from '../../constants/imageConstants';

describe('ReverseSearchLinks', () => {
  it('links to each engine\'s manual upload page when no URL is provided', () => {
    render(<ReverseSearchLinks imageUrl="" />);

    expect(screen.getByText(/no image url provided/i)).toBeInTheDocument();

    REVERSE_SEARCH_ENGINES.forEach((engine) => {
      const link = screen.getByRole('link', { name: engine.name });
      expect(link).toHaveAttribute('href', engine.uploadPage);
    });
  });

  it('builds a url-based reverse-search link for each engine when a URL is provided', () => {
    const imageUrl = 'https://example.com/photo.jpg';
    render(<ReverseSearchLinks imageUrl={imageUrl} />);

    expect(screen.getByText(/open this image in a reverse-search engine/i)).toBeInTheDocument();

    REVERSE_SEARCH_ENGINES.forEach((engine) => {
      const link = screen.getByRole('link', { name: engine.name });
      expect(link).toHaveAttribute('href', engine.urlSearch(imageUrl));
      expect(link.getAttribute('href')).toContain(encodeURIComponent(imageUrl));
    });
  });

  it('trims whitespace from the provided URL before building links', () => {
    render(<ReverseSearchLinks imageUrl="   https://example.com/photo.jpg   " />);

    const link = screen.getByRole('link', { name: 'TinEye' });
    expect(link).toHaveAttribute('href', 'https://tineye.com/search?url=https%3A%2F%2Fexample.com%2Fphoto.jpg');
  });
});

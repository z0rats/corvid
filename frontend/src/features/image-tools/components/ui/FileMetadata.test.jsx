import React from 'react';
import { render, screen } from '@testing-library/react';
import FileMetadata from './FileMetadata';

const FILE_INFO = { format: 'JPEG', mime_type: 'image/jpeg', width: 100, height: 80, mode: 'RGB', file_size: 1024 };
const HASHES = { md5: 'a'.repeat(32), sha1: 'b'.repeat(40), sha256: 'c'.repeat(64) };

describe('FileMetadata', () => {
  it('renders file properties and crypto hashes', () => {
    render(<FileMetadata fileInfo={FILE_INFO} hashes={HASHES} phash={null} />);

    expect(screen.getByText('JPEG')).toBeInTheDocument();
    expect(screen.getByText(HASHES.md5)).toBeInTheDocument();
  });

  it('does not render a pHash row when no phash is provided', () => {
    render(<FileMetadata fileInfo={FILE_INFO} hashes={HASHES} phash={null} />);

    expect(screen.queryByText('pHash')).not.toBeInTheDocument();
  });

  it('renders the pHash hex value and an 8x8 bit matrix when provided', () => {
    const phash = { hex: 'abcdef0123456789', bits: Array(64).fill(true) };

    render(<FileMetadata fileInfo={FILE_INFO} hashes={HASHES} phash={phash} />);

    expect(screen.getByText('pHash')).toBeInTheDocument();
    expect(screen.getByText('abcdef0123456789')).toBeInTheDocument();
  });
});

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import RemoveMetadataPanel from './RemoveMetadataPanel';
import { useImageMetadataRemoval } from '../../hooks/api/useImageMetadataRemoval';

vi.mock('../../hooks/api/useImageMetadataRemoval');

function makeFile() {
  return new File(['fake image content'], 'photo.jpg', { type: 'image/jpeg' });
}

describe('RemoveMetadataPanel', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('defaults to "remove all" mode and downloads with that mode on click', () => {
    const removeMetadata = vi.fn();
    useImageMetadataRemoval.mockReturnValue({ loading: false, error: null, success: false, removeMetadata });
    const file = makeFile();

    render(<RemoveMetadataPanel file={file} />);
    fireEvent.click(screen.getByRole('button', { name: /download cleaned file/i }));

    expect(removeMetadata).toHaveBeenCalledWith(file, 'all');
  });

  it('downloads with location_only mode when that radio is selected', () => {
    const removeMetadata = vi.fn();
    useImageMetadataRemoval.mockReturnValue({ loading: false, error: null, success: false, removeMetadata });
    const file = makeFile();

    render(<RemoveMetadataPanel file={file} />);
    fireEvent.click(screen.getByLabelText(/remove location only/i));
    fireEvent.click(screen.getByRole('button', { name: /download cleaned file/i }));

    expect(removeMetadata).toHaveBeenCalledWith(file, 'location_only');
  });

  it('shows the error message on failure', () => {
    useImageMetadataRemoval.mockReturnValue({ loading: false, error: 'Metadata removal failed', success: false, removeMetadata: vi.fn() });

    render(<RemoveMetadataPanel file={makeFile()} />);

    expect(screen.getByText('Metadata removal failed')).toBeInTheDocument();
  });

  it('shows a success message after a successful download', () => {
    useImageMetadataRemoval.mockReturnValue({ loading: false, error: null, success: true, removeMetadata: vi.fn() });

    render(<RemoveMetadataPanel file={makeFile()} />);

    expect(screen.getByText(/cleaned file downloaded/i)).toBeInTheDocument();
  });

  it('disables the download button while no file has been uploaded', () => {
    useImageMetadataRemoval.mockReturnValue({ loading: false, error: null, success: false, removeMetadata: vi.fn() });

    render(<RemoveMetadataPanel file={null} />);

    expect(screen.getByRole('button', { name: /download cleaned file/i })).toBeDisabled();
  });
});

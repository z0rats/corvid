import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ImageCompareTool from './ImageCompareTool';
import { useImageCompare } from '../../hooks/api/useImageCompare';

vi.mock('../../hooks/api/useImageCompare');

function makeFile(name) {
  return new File(['fake image content'], name, { type: 'image/jpeg' });
}

function fileInputs() {
  return document.querySelectorAll('input[type="file"]');
}

describe('ImageCompareTool', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('disables the Compare button until both files are chosen', async () => {
    useImageCompare.mockReturnValue({ result: null, loading: false, error: null, compareImages: vi.fn() });
    const user = userEvent.setup();

    render(<ImageCompareTool />);
    fireEvent.click(screen.getByText('Compare two images'));

    expect(screen.getByRole('button', { name: 'Compare' })).toBeDisabled();

    const [left, right] = fileInputs();
    await user.upload(left, makeFile('a.jpg'));
    expect(screen.getByRole('button', { name: 'Compare' })).toBeDisabled();

    await user.upload(right, makeFile('b.jpg'));
    expect(screen.getByRole('button', { name: 'Compare' })).toBeEnabled();
  });

  it('calls compareImages with both chosen files', async () => {
    const compareImages = vi.fn();
    useImageCompare.mockReturnValue({ result: null, loading: false, error: null, compareImages });
    const user = userEvent.setup();
    const fileA = makeFile('a.jpg');
    const fileB = makeFile('b.jpg');

    render(<ImageCompareTool />);
    fireEvent.click(screen.getByText('Compare two images'));

    const [left, right] = fileInputs();
    await user.upload(left, fileA);
    await user.upload(right, fileB);
    await user.click(screen.getByRole('button', { name: 'Compare' }));

    expect(compareImages).toHaveBeenCalledWith(fileA, fileB);
  });

  it('shows the error message on failure', () => {
    useImageCompare.mockReturnValue({ result: null, loading: false, error: 'Image comparison failed', compareImages: vi.fn() });

    render(<ImageCompareTool />);
    fireEvent.click(screen.getByText('Compare two images'));

    expect(screen.getByText('Image comparison failed')).toBeInTheDocument();
  });

  it('renders summary chips and the field diff table from a successful result', () => {
    useImageCompare.mockReturnValue({
      result: {
        left: { filename: 'a.jpg' },
        right: { filename: 'b.jpg' },
        field_diffs: [
          { field: 'Image Software', left_value: 'Photoshop', right_value: null, status: 'only_left' },
        ],
        summary: { match_count: 3, differ_count: 1, only_left_count: 1, only_right_count: 0 },
        phash_distance: 2,
        pixels_likely_match: true,
      },
      loading: false,
      error: null,
      compareImages: vi.fn(),
    });

    render(<ImageCompareTool />);
    fireEvent.click(screen.getByText('Compare two images'));

    expect(screen.getByText('3 fields match')).toBeInTheDocument();
    expect(screen.getByText('1 field differs')).toBeInTheDocument();
    expect(screen.getByText(/pixels likely match/i)).toBeInTheDocument();
    expect(screen.getByText('Image Software')).toBeInTheDocument();
    expect(screen.getByText('Photoshop')).toBeInTheDocument();
  });
});

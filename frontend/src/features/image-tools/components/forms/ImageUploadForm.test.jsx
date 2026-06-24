import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ImageUploadForm from './ImageUploadForm';

function makeFile(name = 'photo.jpg', type = 'image/jpeg') {
  return new File(['fake image content'], name, { type });
}

describe('ImageUploadForm', () => {
  it('disables the Analyze button until a file is selected', () => {
    render(
      <ImageUploadForm
        onFileUpload={jest.fn()}
        isLoading={false}
        uploadProgress={0}
        error={null}
      />
    );

    expect(screen.getByRole('button', { name: /analyze/i })).toBeDisabled();
  });

  it('enables Analyze and calls onFileUpload with the selected file when clicked', async () => {
    const onFileUpload = jest.fn();
    const user = userEvent.setup();

    render(
      <ImageUploadForm
        onFileUpload={onFileUpload}
        isLoading={false}
        uploadProgress={0}
        error={null}
      />
    );

    const file = makeFile();
    const input = document.querySelector('input[type="file"]');
    await user.upload(input, file);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /analyze/i })).toBeEnabled();
    });

    await user.click(screen.getByRole('button', { name: /analyze/i }));

    expect(onFileUpload).toHaveBeenCalledTimes(1);
    expect(onFileUpload.mock.calls[0][0].name).toBe('photo.jpg');
  });

  it('shows the error message when provided', () => {
    render(
      <ImageUploadForm
        onFileUpload={jest.fn()}
        isLoading={false}
        uploadProgress={0}
        error="Invalid file type"
      />
    );

    expect(screen.getByText('Invalid file type')).toBeInTheDocument();
  });

  it('disables the dropzone input while loading', () => {
    render(
      <ImageUploadForm
        onFileUpload={jest.fn()}
        isLoading
        uploadProgress={50}
        error={null}
      />
    );

    expect(document.querySelector('input[type="file"]')).toBeDisabled();
  });
});

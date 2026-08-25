import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';
import BackupSettings from './BackupSettings';
import { settingsApi } from '../services/api/settingsApi';

vi.mock('../services/api/settingsApi');

beforeEach(() => {
  settingsApi.getBackupStatus.mockResolvedValue({ supported: true, db_dialect: 'sqlite' });
  window.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
  window.URL.revokeObjectURL = vi.fn();
});

afterEach(() => vi.clearAllMocks());

function renderBackupSettings() {
  return render(
    <MemoryRouter>
      <BackupSettings />
    </MemoryRouter>
  );
}

function backupFile() {
  return new File(['archive-content'], 'backup.tar.gz', { type: 'application/gzip' });
}

describe('BackupSettings — status', () => {
  it('renders the export and restore sections once supported', async () => {
    renderBackupSettings();

    expect(await screen.findByText('Download a backup')).toBeInTheDocument();
    expect(screen.getByText('Restore from a backup')).toBeInTheDocument();
    expect(screen.queryByText(/only supports the SQLite/i)).not.toBeInTheDocument();
  });

  it('shows a warning and disables actions when the dialect is unsupported', async () => {
    settingsApi.getBackupStatus.mockResolvedValue({ supported: false, db_dialect: 'postgresql' });
    renderBackupSettings();

    expect(await screen.findByText(/this deployment runs postgresql/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /download backup/i })).toBeDisabled();
    // The file picker button renders as a <label component="label">, not a real
    // <button> (it wraps the hidden file input), so MUI marks it disabled via
    // aria-disabled rather than the disabled attribute jest-dom's toBeDisabled checks.
    expect(screen.getByRole('button', { name: /choose backup file/i })).toHaveAttribute(
      'aria-disabled',
      'true'
    );
  });
});

describe('BackupSettings — export', () => {
  it('downloads the archive and shows a success notification', async () => {
    const user = userEvent.setup();
    settingsApi.exportBackup.mockResolvedValue({ blob: new Blob(['x']), filename: 'corvid-backup.tar.gz' });
    renderBackupSettings();
    await screen.findByText('Download a backup');

    await user.click(screen.getByRole('button', { name: /download backup/i }));

    await waitFor(() => {
      expect(settingsApi.exportBackup).toHaveBeenCalledWith({
        includeAccessToken: false,
        passphrase: null,
      });
    });
    expect(window.URL.createObjectURL).toHaveBeenCalled();
    expect(await screen.findByText('Backup downloaded.')).toBeInTheDocument();
  });

  it('passes the include-access-token checkbox and passphrase through', async () => {
    const user = userEvent.setup();
    settingsApi.exportBackup.mockResolvedValue({ blob: new Blob(['x']), filename: 'x.tar.gz.enc' });
    renderBackupSettings();
    await screen.findByText('Download a backup');

    await user.click(screen.getByLabelText(/include the access token/i));
    await user.type(screen.getByLabelText(/passphrase \(optional\)/i), 'hunter2');
    await user.click(screen.getByRole('button', { name: /download backup/i }));

    await waitFor(() => {
      expect(settingsApi.exportBackup).toHaveBeenCalledWith({
        includeAccessToken: true,
        passphrase: 'hunter2',
      });
    });
  });

  it('shows an error notification when export fails', async () => {
    const user = userEvent.setup();
    settingsApi.exportBackup.mockRejectedValue(new Error('No encryption key file found'));
    renderBackupSettings();
    await screen.findByText('Download a backup');

    await user.click(screen.getByRole('button', { name: /download backup/i }));

    expect(await screen.findByText('No encryption key file found')).toBeInTheDocument();
    expect(window.URL.createObjectURL).not.toHaveBeenCalled();
  });
});

describe('BackupSettings — restore', () => {
  it('keeps the restore button disabled until a file is chosen', async () => {
    renderBackupSettings();
    await screen.findByText('Restore from a backup');

    expect(screen.getByRole('button', { name: 'Restore' })).toBeDisabled();
  });

  it('requires typing RESTORE in the confirmation dialog before proceeding', async () => {
    const user = userEvent.setup();
    renderBackupSettings();
    await screen.findByText('Restore from a backup');

    const fileInput = document.querySelector('input[type="file"]');
    await user.upload(fileInput, backupFile());
    await user.click(screen.getByRole('button', { name: 'Restore' }));

    expect(await screen.findByText('Confirm restore')).toBeInTheDocument();
    // MUI's Modal marks everything outside the dialog aria-hidden while it's open,
    // so the card's own "Restore" button drops out of the accessible query - scope
    // to the dialog to find its confirm button unambiguously.
    const dialog = screen.getByRole('dialog');
    const confirmButton = within(dialog).getByRole('button', { name: 'Restore' });
    expect(confirmButton).toBeDisabled();

    await user.type(screen.getByLabelText(/type "restore" to confirm/i), 'RESTORE');
    expect(confirmButton).toBeEnabled();

    settingsApi.restoreBackup.mockResolvedValue({ restart_required: true, access_token_restored: false });
    await user.click(confirmButton);

    await waitFor(() => {
      expect(settingsApi.restoreBackup).toHaveBeenCalledWith({
        file: expect.any(File),
        passphrase: null,
      });
    });
    expect(
      await screen.findByText('Restore complete. Restart the backend for the restored data to take effect.')
    ).toBeInTheDocument();
  });

  it('shows the access-token-restored message when the backup included one', async () => {
    const user = userEvent.setup();
    settingsApi.restoreBackup.mockResolvedValue({ restart_required: true, access_token_restored: true });
    renderBackupSettings();
    await screen.findByText('Restore from a backup');

    const fileInput = document.querySelector('input[type="file"]');
    await user.upload(fileInput, backupFile());
    await user.click(screen.getByRole('button', { name: 'Restore' }));
    await user.type(await screen.findByLabelText(/type "restore" to confirm/i), 'RESTORE');
    await user.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Restore' }));

    expect(await screen.findByText(/the access token was also restored/i)).toBeInTheDocument();
  });

  it('shows an error notification when restore fails', async () => {
    const user = userEvent.setup();
    settingsApi.restoreBackup.mockRejectedValue({
      response: { data: { detail: 'Incorrect passphrase, or the backup file is corrupted.' } },
    });
    renderBackupSettings();
    await screen.findByText('Restore from a backup');

    const fileInput = document.querySelector('input[type="file"]');
    await user.upload(fileInput, backupFile());
    await user.click(screen.getByRole('button', { name: 'Restore' }));
    await user.type(await screen.findByLabelText(/type "restore" to confirm/i), 'RESTORE');
    await user.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Restore' }));

    expect(
      await screen.findByText('Incorrect passphrase, or the backup file is corrupted.')
    ).toBeInTheDocument();
  });
});

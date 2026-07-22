import React from 'react';
import { getDefaultStore } from 'jotai';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import CommandPaletteSettings from './CommandPaletteSettings';
import { settingsApi } from '../services/api/settingsApi';
import { savePlaybook, getPlaybook } from '../../../core/utils/commandPaletteStorage';
import { generalSettingsState } from '../../../core/state/atoms';

vi.mock('../services/api/settingsApi');

beforeEach(() => {
  localStorage.clear();
  // generalSettingsState uses jotai's implicit global default store (no <Provider> in tests),
  // so it persists across tests in this file unless reset explicitly.
  getDefaultStore().set(generalSettingsState, {});
  settingsApi.updateCommandPaletteSettings.mockResolvedValue({
    id: 1,
    darkmode: false,
    language: 'en',
    auto_open_on_single_match: false,
    start_screen: 'newsfeed',
    always_tiles: true,
  });
});

afterEach(() => {
  vi.clearAllMocks();
});

function renderSettings() {
  return render(
    <MemoryRouter>
      <CommandPaletteSettings />
    </MemoryRouter>,
  );
}

describe('CommandPaletteSettings', () => {
  it('renders the three settings fields with their defaults', () => {
    renderSettings();

    expect(screen.getByText('Command Palette')).toBeInTheDocument();
    expect(screen.getByLabelText(/auto-open on single match/i)).toBeChecked();
    expect(screen.getByLabelText(/always use tiles/i)).not.toBeChecked();
  });

  it('toggling auto-open calls the API with the flipped value', async () => {
    const user = userEvent.setup();
    renderSettings();

    await user.click(screen.getByLabelText(/auto-open on single match/i));

    expect(settingsApi.updateCommandPaletteSettings).toHaveBeenCalledWith({
      autoOpenOnSingleMatch: false,
    });
  });

  it('changing the start screen select calls the API', async () => {
    renderSettings();

    const select = screen.getByRole('combobox');
    fireEvent.mouseDown(select);
    const option = await screen.findByRole('option', { name: 'Newsfeed' });
    fireEvent.click(option);

    await waitFor(() => {
      expect(settingsApi.updateCommandPaletteSettings).toHaveBeenCalledWith({
        startScreen: 'newsfeed',
      });
    });
  });

  it('shows a success notification after a successful update', async () => {
    const user = userEvent.setup();
    renderSettings();

    await user.click(screen.getByLabelText(/always use tiles/i));

    expect(await screen.findByText(/updated successfully/i)).toBeInTheDocument();
  });
});

describe('CommandPaletteSettings — playbook management', () => {
  it('shows the empty state with no saved playbooks', () => {
    renderSettings();
    expect(screen.getByText(/no saved playbooks yet/i)).toBeInTheDocument();
  });

  it('lists a saved playbook with its step trail', () => {
    savePlaybook('identity-triage', ['reddit_search']);
    renderSettings();

    expect(screen.getByText('identity-triage')).toBeInTheDocument();
  });

  it('deletes a playbook', async () => {
    const user = userEvent.setup();
    savePlaybook('to-delete', ['reddit_search']);
    renderSettings();

    expect(screen.getByText('to-delete')).toBeInTheDocument();
    await user.click(screen.getByLabelText('Delete'));

    expect(screen.queryByText('to-delete')).not.toBeInTheDocument();
    expect(getPlaybook('to-delete')).toBeNull();
  });

  it('renames a playbook', async () => {
    const user = userEvent.setup();
    savePlaybook('old-name', ['reddit_search']);
    renderSettings();

    await user.click(screen.getByLabelText('Rename'));
    const input = screen.getByDisplayValue('old-name');
    await user.clear(input);
    await user.type(input, 'new-name');
    await user.click(screen.getByLabelText('Confirm rename'));

    expect(screen.getByText('new-name')).toBeInTheDocument();
    expect(getPlaybook('old-name')).toBeNull();
  });
});

import React from 'react';
import { getDefaultStore } from 'jotai';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';
import GeneralSettings from './GeneralSettings';
import { settingsApi } from '../services/api/settingsApi';
import { generalSettingsState, themeModeAtom } from '../../../core/state/atoms';
import i18n from '../../../core/i18n';

vi.mock('../services/api/settingsApi');

beforeEach(() => {
  localStorage.clear();
  // generalSettingsState/themeModeAtom live in jotai's implicit default store (no <Provider>).
  getDefaultStore().set(generalSettingsState, {});
  getDefaultStore().set(themeModeAtom, 'light');
  settingsApi.updateLanguage.mockResolvedValue({});
  settingsApi.updateCommandPaletteSettings.mockResolvedValue({
    start_screen: 'newsfeed',
    always_tiles: true,
  });
});

afterEach(async () => {
  vi.clearAllMocks();
  // updateLanguage switches the real global i18n instance - reset it so later tests stay English.
  await i18n.changeLanguage('en');
});

function renderSettings() {
  return render(
    <MemoryRouter>
      <GeneralSettings />
    </MemoryRouter>,
  );
}

async function pickOption(selectLabel, optionName) {
  fireEvent.mouseDown(screen.getByRole('combobox', { name: selectLabel }));
  fireEvent.click(await screen.findByRole('option', { name: optionName }));
}

describe('GeneralSettings', () => {
  it('renders language, theme, start screen and tiles with their defaults', () => {
    renderSettings();

    expect(screen.getByRole('combobox', { name: 'Language' })).toHaveTextContent('English');
    expect(screen.getByRole('combobox', { name: 'Theme' })).toHaveTextContent('Light');
    expect(screen.getByRole('combobox', { name: 'Start screen' })).toHaveTextContent('Search');
    expect(screen.getByLabelText(/always use tiles/i)).not.toBeChecked();
    expect(screen.getByText(/russian translation is incomplete/i)).toBeInTheDocument();
  });

  it('changing the language calls the language API', async () => {
    renderSettings();

    await pickOption('Language', 'Русский');

    await waitFor(() => expect(settingsApi.updateLanguage).toHaveBeenCalledWith('ru'));
  });

  it('changing the theme updates the theme atom without an API call', async () => {
    renderSettings();

    await pickOption('Theme', 'Dark');

    await waitFor(() => expect(getDefaultStore().get(themeModeAtom)).toBe('dark'));
    expect(settingsApi.updateCommandPaletteSettings).not.toHaveBeenCalled();
  });

  it('changing the start screen calls the API', async () => {
    renderSettings();

    await pickOption('Start screen', 'Newsfeed');

    await waitFor(() => {
      expect(settingsApi.updateCommandPaletteSettings).toHaveBeenCalledWith({ startScreen: 'newsfeed' });
    });
  });

  it('toggling tiles sends the flipped default and confirms', async () => {
    const user = userEvent.setup();
    renderSettings();

    await user.click(screen.getByLabelText(/always use tiles/i));

    expect(settingsApi.updateCommandPaletteSettings).toHaveBeenCalledWith({ alwaysTiles: true });
    expect(await screen.findByText(/updated successfully/i)).toBeInTheDocument();
  });
});

import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import ApiKeyInput from './ApiKeyInput';
import GhuntSessionInput from './GhuntSessionInput';
import { useApiKeys } from '../../hooks/api/useApiKeys';

vi.mock('../../hooks/api/useApiKeys', () => ({ useApiKeys: vi.fn() }));

let api;
beforeEach(() => {
  api = {
    loading: false,
    getKeyStatus: vi.fn().mockResolvedValue({ success: true, data: { existsInBackend: false, isServiceActive: false } }),
    saveApiKey: vi.fn().mockResolvedValue({ success: true, message: 'API key saved' }),
    saveGhuntSession: vi.fn().mockResolvedValue({ success: true, message: 'Session saved' }),
    deleteApiKey: vi.fn().mockResolvedValue({ success: true, message: 'Deleted' }),
    toggleServiceActivation: vi.fn().mockResolvedValue({ success: true, isActive: false, message: 'Deactivated' }),
  };
  // getKeyStatus must stay referentially stable, as the real hook's useCallback is
  useApiKeys.mockImplementation(() => api);
});

const configured = () => api.getKeyStatus.mockResolvedValue({ success: true, data: { existsInBackend: true, isServiceActive: true } });

describe('ApiKeyInput', () => {
  // awaits the initial status load, which resets the field
  const renderInput = async () => {
    render(<ApiKeyInput name="crowdstrike_client_id" description="CrowdStrike ID" link="https://falcon.example" relatedKeys={['crowdstrike_client_secret']} />);
    await act(async () => {});
  };

  it('asks for the key status of this key plus its related keys', async () => {
    await renderInput();
    await waitFor(() => expect(api.getKeyStatus).toHaveBeenCalledWith('crowdstrike_client_id', ['crowdstrike_client_secret']));
  });

  it('saves a typed key, then masks it and locks the field', async () => {
    await renderInput();
    const field = screen.getByLabelText('CrowdStrike ID');
    const save = screen.getByRole('button', { name: 'Save API key' });
    expect(save).toBeDisabled();

    fireEvent.change(field, { target: { value: 'sk-secret' } });
    fireEvent.click(save);

    await waitFor(() => expect(api.saveApiKey).toHaveBeenCalledWith('crowdstrike_client_id', 'sk-secret'));
    expect(await screen.findByText('API key saved')).toBeInTheDocument();
    expect(field).toHaveValue('••••••••••••••••');
    expect(field).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Delete API key' })).toBeInTheDocument();
  });

  it('never renders a configured key, only the mask', async () => {
    configured();
    await renderInput();
    const field = screen.getByLabelText('CrowdStrike ID');
    await waitFor(() => expect(field).toHaveValue('••••••••••••••••'));
    expect(field).toHaveAttribute('type', 'password');
  });

  it('delete clears the configured state', async () => {
    configured();
    await renderInput();
    fireEvent.click(await screen.findByRole('button', { name: 'Delete API key' }));
    await waitFor(() => expect(api.deleteApiKey).toHaveBeenCalledWith('crowdstrike_client_id'));
    expect(await screen.findByRole('button', { name: 'Save API key' })).toBeInTheDocument();
    expect(screen.getByLabelText('CrowdStrike ID')).toHaveValue('');
  });

  it('toggle (de)activates the key together with its related keys', async () => {
    configured();
    await renderInput();
    const toggle = screen.getByRole('switch');
    await waitFor(() => expect(toggle).toBeChecked());
    fireEvent.click(toggle);
    await waitFor(() => expect(api.toggleServiceActivation).toHaveBeenCalledWith(
      ['crowdstrike_client_id', 'crowdstrike_client_secret'], true, 'CrowdStrike ID',
    ));
    await waitFor(() => expect(toggle).not.toBeChecked());
  });

  it('surfaces API failures as notifications and keeps state', async () => {
    api.saveApiKey.mockResolvedValue({ success: false, message: 'Save failed' });
    await renderInput();
    fireEvent.change(screen.getByLabelText('CrowdStrike ID'), { target: { value: 'k' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save API key' }));
    expect(await screen.findByText('Save failed')).toBeInTheDocument();
    expect(screen.getByLabelText('CrowdStrike ID')).toHaveValue('k');
  });

  it('a failed status load shows its message', async () => {
    api.getKeyStatus.mockResolvedValue({ success: false, message: 'Status unavailable' });
    await renderInput();
    expect(await screen.findByText('Status unavailable')).toBeInTheDocument();
  });

  it('the "get a key" links open the provider safely in a new tab', async () => {
    await renderInput();
    for (const link of screen.getAllByRole('link')) {
      expect(link).toHaveAttribute('href', 'https://falcon.example');
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    }
  });
});

describe('GhuntSessionInput', () => {
  const renderInput = async () => {
    render(<GhuntSessionInput name="ghunt_session" description="GHunt session" />);
    await act(async () => {});
  };

  it('saves through the validating session endpoint and clears the pasted blob', async () => {
    await renderInput();
    const field = screen.getByLabelText('GHunt session');
    fireEvent.change(field, { target: { value: 'eyJjb29raWVzIjp7fX0=' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save GHunt session' }));
    await waitFor(() => expect(api.saveGhuntSession).toHaveBeenCalledWith('eyJjb29raWVzIjp7fX0='));
    expect(api.saveApiKey).not.toHaveBeenCalled();
    await waitFor(() => expect(field).toHaveValue(''));
    expect(field).toBeDisabled();
  });

  it('whitespace-only paste cannot be saved', async () => {
    await renderInput();
    fireEvent.change(screen.getByLabelText('GHunt session'), { target: { value: '  \n ' } });
    expect(screen.getByRole('button', { name: 'Save GHunt session' })).toBeDisabled();
  });

  it('a rejected session keeps the paste for correction', async () => {
    api.saveGhuntSession.mockResolvedValue({ success: false, message: 'Invalid GHunt session' });
    await renderInput();
    const field = screen.getByLabelText('GHunt session');
    fireEvent.change(field, { target: { value: 'garbage' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save GHunt session' }));
    expect(await screen.findByText('Invalid GHunt session')).toBeInTheDocument();
    expect(field).toHaveValue('garbage');
  });

  it('configured session is never echoed back; delete and toggle work', async () => {
    configured();
    await renderInput();
    const field = screen.getByLabelText('GHunt session');
    fireEvent.click(await screen.findByRole('button', { name: 'Delete GHunt session' }));
    expect(field).toHaveValue('');
    await waitFor(() => expect(api.deleteApiKey).toHaveBeenCalledWith('ghunt_session'));

    fireEvent.click(screen.getByRole('switch'));
    await waitFor(() => expect(api.toggleServiceActivation).toHaveBeenCalledWith(['ghunt_session'], false, 'GHunt session'));
  });
});

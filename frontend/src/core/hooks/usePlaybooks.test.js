import { act, renderHook } from '@testing-library/react';
import { usePlaybooks } from './usePlaybooks';
import { getPlaybooks } from '../utils/commandPaletteStorage';

const registry = [
  { id: 'reddit', label: 'Reddit Search' },
  { id: 'whois', label: 'WHOIS' },
  { id: 'shodan', label: 'Shodan' },
];

function setup() {
  const onOpenEntry = vi.fn();
  const setBreadcrumbs = vi.fn();
  const showNotice = vi.fn();
  const { result } = renderHook(() => usePlaybooks(registry, { onOpenEntry, setBreadcrumbs, showNotice }));
  return { result, onOpenEntry, setBreadcrumbs, showNotice };
}

beforeEach(() => {
  localStorage.clear();
});

describe('usePlaybooks — recording lifecycle', () => {
  it('accumulates unique steps via recordStep while recording', () => {
    const { result } = setup();

    act(() => result.current.startRecording());
    expect(result.current.isRecording).toBe(true);
    expect(result.current.recordingSteps).toEqual([]);

    act(() => result.current.recordStep('reddit'));
    act(() => result.current.recordStep('whois'));
    act(() => result.current.recordStep('reddit')); // duplicate, ignored

    expect(result.current.recordingSteps).toEqual(['reddit', 'whois']);
  });

  it('finishRecording with a name persists the playbook and stops recording', () => {
    const { result, showNotice } = setup();

    act(() => result.current.startRecording());
    act(() => result.current.recordStep('reddit'));
    act(() => result.current.recordStep('whois'));
    act(() => result.current.finishRecording('recon-chain'));

    expect(result.current.isRecording).toBe(false);
    expect(result.current.recordingSteps).toEqual([]);
    expect(getPlaybooks()).toEqual([
      expect.objectContaining({ name: 'recon-chain', steps: ['reddit', 'whois'] }),
    ]);
    expect(result.current.playbooks).toEqual([
      expect.objectContaining({ name: 'recon-chain', steps: ['reddit', 'whois'] }),
    ]);
    expect(showNotice).toHaveBeenCalledWith(expect.stringContaining('recon-chain'));
  });

  it('finishRecording with no name or no steps discards the recording without saving', () => {
    const { result, showNotice } = setup();

    act(() => result.current.startRecording());
    act(() => result.current.recordStep('reddit'));
    act(() => result.current.finishRecording(null));

    expect(result.current.isRecording).toBe(false);
    expect(result.current.recordingSteps).toEqual([]);
    expect(getPlaybooks()).toEqual([]);
    expect(showNotice).not.toHaveBeenCalled();
  });

  it('requestRecordStopName / cancelRecordStopPrompt toggle the pending-name prompt', () => {
    const { result } = setup();

    act(() => result.current.requestRecordStopName());
    expect(result.current.pendingRecordStopName).toBe(true);

    act(() => result.current.cancelRecordStopPrompt());
    expect(result.current.pendingRecordStopName).toBe(false);
  });
});

describe('usePlaybooks — runPlaybook', () => {
  it('opens the first step via onOpenEntry and seeds the rest as pending breadcrumbs', () => {
    const { result, onOpenEntry, setBreadcrumbs } = setup();

    act(() => result.current.startRecording());
    act(() => result.current.recordStep('reddit'));
    act(() => result.current.recordStep('whois'));
    act(() => result.current.recordStep('shodan'));
    act(() => result.current.finishRecording('triage'));

    act(() => result.current.runPlaybook('triage', 'john_doe'));

    expect(onOpenEntry).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'reddit' }),
      'john_doe',
    );
    expect(setBreadcrumbs).toHaveBeenCalledTimes(1);
    const updater = setBreadcrumbs.mock.calls[0][0];
    expect(updater([])).toEqual([
      { label: 'WHOIS', toolId: 'whois', pending: true },
      { label: 'Shodan', toolId: 'shodan', pending: true },
    ]);
  });

  it('does not touch breadcrumbs for a single-step playbook', () => {
    const { result, onOpenEntry, setBreadcrumbs } = setup();

    act(() => result.current.startRecording());
    act(() => result.current.recordStep('reddit'));
    act(() => result.current.finishRecording('single-step'));

    act(() => result.current.runPlaybook('single-step', null));

    expect(onOpenEntry).toHaveBeenCalledWith(expect.objectContaining({ id: 'reddit' }), null);
    expect(setBreadcrumbs).not.toHaveBeenCalled();
  });

  it('shows a not-found notice and does not open anything for an unknown playbook', () => {
    const { result, onOpenEntry, showNotice } = setup();

    act(() => result.current.runPlaybook('does-not-exist', null));

    expect(onOpenEntry).not.toHaveBeenCalled();
    expect(showNotice).toHaveBeenCalledWith(expect.stringContaining('does-not-exist'), 'error');
  });

  it('shows a not-found notice when the recorded step no longer exists in the registry', () => {
    const { result, onOpenEntry, showNotice } = setup();

    act(() => result.current.startRecording());
    act(() => result.current.recordStep('removed-tool'));
    act(() => result.current.finishRecording('stale'));

    act(() => result.current.runPlaybook('stale', null));

    expect(onOpenEntry).not.toHaveBeenCalled();
    expect(showNotice).toHaveBeenCalledWith(expect.stringContaining('stale'), 'error');
  });
});

describe('usePlaybooks — rename/delete', () => {
  it('renamePlaybook persists via storage and refreshes local state', () => {
    const { result } = setup();
    act(() => result.current.startRecording());
    act(() => result.current.recordStep('reddit'));
    act(() => result.current.finishRecording('old-name'));

    act(() => result.current.renamePlaybook('old-name', 'new-name'));

    expect(result.current.playbooks.map((p) => p.name)).toEqual(['new-name']);
    expect(getPlaybooks().map((p) => p.name)).toEqual(['new-name']);
  });

  it('deletePlaybook persists via storage and refreshes local state', () => {
    const { result } = setup();
    act(() => result.current.startRecording());
    act(() => result.current.recordStep('reddit'));
    act(() => result.current.finishRecording('to-delete'));

    act(() => result.current.deletePlaybook('to-delete'));

    expect(result.current.playbooks).toEqual([]);
    expect(getPlaybooks()).toEqual([]);
  });
});

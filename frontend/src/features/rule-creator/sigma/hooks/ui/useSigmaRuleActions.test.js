import { act, renderHook } from '@testing-library/react';
import { useSigmaRuleActions } from './useSigmaRuleActions';
import * as sigmaRuleService from '../../services/sigmaRuleService';

function fakeRuleState(overrides = {}) {
  return {
    metadata: {
      title: 'My Rule',
      id: 'abc-123',
      status: 'experimental',
      description: '',
      authors: [],
      date: '',
      modified: '',
      license: '',
      level: 'high',
    },
    logSource: { product: '', category: '', service: '', definition: '' },
    detections: { filter: '', condition: '', timeframe: '' },
    conditionsList: [],
    fields: [],
    references: [],
    tags: [],
    falsePositives: [],
    resetAll: vi.fn(),
    ...overrides,
  };
}

describe('useSigmaRuleActions — isRuleValid', () => {
  it('is truthy when title and id are both set', () => {
    const { result } = renderHook(() => useSigmaRuleActions(fakeRuleState()));
    expect(result.current.isRuleValid()).toBeTruthy();
  });

  it('is falsy when the title is blank', () => {
    const ruleState = fakeRuleState({ metadata: { title: '  ', id: 'abc' } });
    const { result } = renderHook(() => useSigmaRuleActions(ruleState));
    expect(result.current.isRuleValid()).toBeFalsy();
  });
});

describe('useSigmaRuleActions — handlePreview', () => {
  it('generates the rule and opens the preview on success', () => {
    const { result } = renderHook(() => useSigmaRuleActions(fakeRuleState()));

    act(() => result.current.handlePreview());

    expect(result.current.previewOpen).toBe(true);
    expect(result.current.rulePreview).toContain('title: My Rule');
    expect(result.current.errorAlert.open).toBe(false);
  });

  it('shows an error alert instead of opening the preview when generation fails', () => {
    const ruleState = fakeRuleState({ metadata: { title: '', id: '' } });
    const { result } = renderHook(() => useSigmaRuleActions(ruleState));

    act(() => result.current.handlePreview());

    expect(result.current.previewOpen).toBe(false);
    expect(result.current.errorAlert.open).toBe(true);
    expect(result.current.errorAlert.message).toContain('title is required');
  });
});

describe('useSigmaRuleActions — handleExport', () => {
  it('generates the rule and delegates to exportSigmaRule', () => {
    const exportSpy = vi.spyOn(sigmaRuleService, 'exportSigmaRule').mockImplementation(() => {});
    const { result } = renderHook(() => useSigmaRuleActions(fakeRuleState()));

    act(() => result.current.handleExport());

    expect(exportSpy).toHaveBeenCalledWith(expect.stringContaining('title: My Rule'), 'My Rule');
    exportSpy.mockRestore();
  });

  it('shows an error alert instead of exporting when generation fails', () => {
    const exportSpy = vi.spyOn(sigmaRuleService, 'exportSigmaRule').mockImplementation(() => {});
    const ruleState = fakeRuleState({ metadata: { title: '', id: '' } });
    const { result } = renderHook(() => useSigmaRuleActions(ruleState));

    act(() => result.current.handleExport());

    expect(exportSpy).not.toHaveBeenCalled();
    expect(result.current.errorAlert.open).toBe(true);
    exportSpy.mockRestore();
  });
});

describe('useSigmaRuleActions — handleReset', () => {
  it('requests confirmation without resetting immediately', () => {
    const ruleState = fakeRuleState();
    const { result } = renderHook(() => useSigmaRuleActions(ruleState));

    act(() => result.current.handleReset());

    expect(ruleState.resetAll).not.toHaveBeenCalled();
    expect(result.current.confirmDialog.open).toBe(true);
  });

  it('resets the form and closes the preview once confirmed', () => {
    const ruleState = fakeRuleState();
    const { result } = renderHook(() => useSigmaRuleActions(ruleState));
    act(() => result.current.handlePreview());
    act(() => result.current.handleReset());

    act(() => result.current.onConfirmReset());

    expect(ruleState.resetAll).toHaveBeenCalledTimes(1);
    expect(result.current.previewOpen).toBe(false);
    expect(result.current.rulePreview).toBe('');
  });

  it('does not reset when the confirmation is cancelled', () => {
    const ruleState = fakeRuleState();
    const { result } = renderHook(() => useSigmaRuleActions(ruleState));
    act(() => result.current.handleReset());

    act(() => result.current.onCancelReset());

    expect(ruleState.resetAll).not.toHaveBeenCalled();
  });
});

describe('useSigmaRuleActions — handleClosePreview', () => {
  it('closes the preview and clears its content', () => {
    const { result } = renderHook(() => useSigmaRuleActions(fakeRuleState()));
    act(() => result.current.handlePreview());

    act(() => result.current.handleClosePreview());

    expect(result.current.previewOpen).toBe(false);
    expect(result.current.rulePreview).toBe('');
  });
});

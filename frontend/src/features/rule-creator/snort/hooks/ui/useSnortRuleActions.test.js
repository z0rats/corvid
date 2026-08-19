import { act, renderHook } from '@testing-library/react';
import { useSnortRuleActions } from './useSnortRuleActions';
import * as snortRuleService from '../../services/snortRuleService';

function fakeRuleState(overrides = {}) {
  return {
    ruleHeader: {
      action: 'alert',
      protocol: 'tcp',
      sourceIP: 'any',
      sourcePort: 'any',
      direction: '->',
      destIP: 'any',
      destPort: 'any',
    },
    ruleOptions: {
      msg: 'Suspicious traffic',
      sid: '1000001',
      rev: '1',
      classtype: '',
      priority: '',
      reference: [],
      metadata: [],
    },
    ruleContent: { content: [], pcre: [], flowbits: [], threshold: '', detection_filter: '' },
    ruleMetadata: {},
    resetAll: vi.fn(),
    ...overrides,
  };
}

describe('useSnortRuleActions — isRuleValid', () => {
  it('is truthy when msg and sid are both set', () => {
    const { result } = renderHook(() => useSnortRuleActions(fakeRuleState()));
    expect(result.current.isRuleValid()).toBeTruthy();
  });

  it('is falsy when sid is blank', () => {
    const ruleState = fakeRuleState({ ruleOptions: { msg: 'x', sid: '  ', reference: [], metadata: [] } });
    const { result } = renderHook(() => useSnortRuleActions(ruleState));
    expect(result.current.isRuleValid()).toBeFalsy();
  });
});

describe('useSnortRuleActions — handlePreview', () => {
  it('generates the rule and opens the preview on success', () => {
    const { result } = renderHook(() => useSnortRuleActions(fakeRuleState()));

    act(() => result.current.handlePreview());

    expect(result.current.previewOpen).toBe(true);
    expect(result.current.rulePreview).toContain('msg:"Suspicious traffic"');
  });

  it('shows an error alert when a required option is missing', () => {
    const ruleState = fakeRuleState({
      ruleOptions: { msg: '', sid: '', rev: '1', reference: [], metadata: [] },
    });
    const { result } = renderHook(() => useSnortRuleActions(ruleState));

    act(() => result.current.handlePreview());

    expect(result.current.previewOpen).toBe(false);
    expect(result.current.errorAlert.open).toBe(true);
  });
});

describe('useSnortRuleActions — handleExport', () => {
  it('generates the rule and delegates to exportSnortRule with the sid', () => {
    const exportSpy = vi.spyOn(snortRuleService, 'exportSnortRule').mockImplementation(() => {});
    const { result } = renderHook(() => useSnortRuleActions(fakeRuleState()));

    act(() => result.current.handleExport());

    expect(exportSpy).toHaveBeenCalledWith(expect.stringContaining('Suspicious traffic'), '1000001');
    exportSpy.mockRestore();
  });
});

describe('useSnortRuleActions — handleReset', () => {
  it('only resets after confirmation', () => {
    const ruleState = fakeRuleState();
    const { result } = renderHook(() => useSnortRuleActions(ruleState));

    act(() => result.current.handleReset());
    expect(ruleState.resetAll).not.toHaveBeenCalled();

    act(() => result.current.onConfirmReset());
    expect(ruleState.resetAll).toHaveBeenCalledTimes(1);
    expect(result.current.previewOpen).toBe(false);
  });
});

describe('useSnortRuleActions — handleClosePreview', () => {
  it('closes the preview and clears its content', () => {
    const { result } = renderHook(() => useSnortRuleActions(fakeRuleState()));
    act(() => result.current.handlePreview());

    act(() => result.current.handleClosePreview());

    expect(result.current.previewOpen).toBe(false);
    expect(result.current.rulePreview).toBe('');
  });
});

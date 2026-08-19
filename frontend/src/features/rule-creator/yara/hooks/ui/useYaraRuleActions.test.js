import { act, renderHook } from '@testing-library/react';
import { useYaraRuleActions } from './useYaraRuleActions';
import * as yaraRuleService from '../../services/yaraRuleService';

function fakeRuleState(overrides = {}) {
  return {
    metadata: { ruleName: 'My Rule', author: 'analyst' },
    strings: [],
    conditions: {},
    currentString: { identifier: '', type: 'text', value: '', modifiers: [] },
    tags: [],
    currentTag: '',
    addString: vi.fn(),
    removeString: vi.fn(),
    resetCurrentString: vi.fn(),
    addTag: vi.fn(),
    removeTag: vi.fn(),
    resetCurrentTag: vi.fn(),
    resetAll: vi.fn(),
    ...overrides,
  };
}

describe('useYaraRuleActions — handleAddString', () => {
  it('adds a trimmed string and resets the draft on success', () => {
    const ruleState = fakeRuleState({
      currentString: { identifier: '  my_str  ', type: 'text', value: '  evil  ', modifiers: [] },
    });
    const { result } = renderHook(() => useYaraRuleActions(ruleState));

    let returned;
    act(() => {
      returned = result.current.handleAddString();
    });

    expect(returned).toBe(true);
    expect(ruleState.addString).toHaveBeenCalledWith({
      identifier: 'my_str',
      type: 'text',
      value: 'evil',
      modifiers: [],
    });
    expect(ruleState.resetCurrentString).toHaveBeenCalledTimes(1);
    expect(result.current.errors).toEqual({});
  });

  it('sets an identifier error and does not add the string when the identifier is invalid', () => {
    const ruleState = fakeRuleState({
      currentString: { identifier: '1bad', type: 'text', value: 'x', modifiers: [] },
    });
    const { result } = renderHook(() => useYaraRuleActions(ruleState));

    let returned;
    act(() => {
      returned = result.current.handleAddString();
    });

    expect(returned).toBe(false);
    expect(ruleState.addString).not.toHaveBeenCalled();
    expect(result.current.errors.identifier).toBeTruthy();
  });

  it('sets a value error when the value is invalid for the given type', () => {
    const ruleState = fakeRuleState({
      currentString: { identifier: 'a', type: 'hex', value: 'not hex', modifiers: [] },
    });
    const { result } = renderHook(() => useYaraRuleActions(ruleState));

    act(() => result.current.handleAddString());

    expect(ruleState.addString).not.toHaveBeenCalled();
    expect(result.current.errors.value).toBeTruthy();
  });
});

describe('useYaraRuleActions — handleDeleteString', () => {
  it('delegates to removeString', () => {
    const ruleState = fakeRuleState();
    const { result } = renderHook(() => useYaraRuleActions(ruleState));

    act(() => result.current.handleDeleteString('id-1'));

    expect(ruleState.removeString).toHaveBeenCalledWith('id-1');
  });
});

describe('useYaraRuleActions — handleAddTag / handleDeleteTag', () => {
  it('adds a non-blank tag and resets the draft', () => {
    const ruleState = fakeRuleState({ currentTag: 'malware' });
    const { result } = renderHook(() => useYaraRuleActions(ruleState));

    act(() => result.current.handleAddTag());

    expect(ruleState.addTag).toHaveBeenCalledWith('malware');
    expect(ruleState.resetCurrentTag).toHaveBeenCalledTimes(1);
  });

  it('does not add a blank tag', () => {
    const ruleState = fakeRuleState({ currentTag: '   ' });
    const { result } = renderHook(() => useYaraRuleActions(ruleState));

    act(() => result.current.handleAddTag());

    expect(ruleState.addTag).not.toHaveBeenCalled();
  });

  it('handleDeleteTag delegates to removeTag', () => {
    const ruleState = fakeRuleState();
    const { result } = renderHook(() => useYaraRuleActions(ruleState));

    act(() => result.current.handleDeleteTag('id-1'));

    expect(ruleState.removeTag).toHaveBeenCalledWith('id-1');
  });
});

describe('useYaraRuleActions — handlePreview / handleExport', () => {
  it('handlePreview opens the preview with the generated rule when the rule name is valid', () => {
    const { result } = renderHook(() => useYaraRuleActions(fakeRuleState()));

    act(() => result.current.handlePreview());

    expect(result.current.previewOpen).toBe(true);
    expect(result.current.rulePreview).toContain('rule My_Rule');
  });

  it('handlePreview sets a ruleName error and does not open the preview for an invalid name', () => {
    const ruleState = fakeRuleState({ metadata: { ruleName: '1bad', author: '' } });
    const { result } = renderHook(() => useYaraRuleActions(ruleState));

    act(() => result.current.handlePreview());

    expect(result.current.previewOpen).toBe(false);
    expect(result.current.errors.ruleName).toBeTruthy();
  });

  it('handleExport delegates to exportYaraRule when the rule name is valid', () => {
    const exportSpy = vi.spyOn(yaraRuleService, 'exportYaraRule').mockImplementation(() => {});
    const { result } = renderHook(() => useYaraRuleActions(fakeRuleState()));

    act(() => result.current.handleExport());

    expect(exportSpy).toHaveBeenCalledWith(expect.stringContaining('rule My_Rule'), 'My Rule');
    exportSpy.mockRestore();
  });

  it('handleExport sets a ruleName error instead of exporting for an invalid name', () => {
    const exportSpy = vi.spyOn(yaraRuleService, 'exportYaraRule').mockImplementation(() => {});
    const ruleState = fakeRuleState({ metadata: { ruleName: '', author: '' } });
    const { result } = renderHook(() => useYaraRuleActions(ruleState));

    act(() => result.current.handleExport());

    expect(exportSpy).not.toHaveBeenCalled();
    expect(result.current.errors.ruleName).toBeTruthy();
    exportSpy.mockRestore();
  });
});

describe('useYaraRuleActions — validity helpers', () => {
  it('isValidForPreview/isValidForExport reflect the rule name validity', () => {
    const valid = renderHook(() => useYaraRuleActions(fakeRuleState()));
    expect(valid.result.current.isValidForPreview()).toBe(true);
    expect(valid.result.current.isValidForExport()).toBe(true);

    const invalid = renderHook(() =>
      useYaraRuleActions(fakeRuleState({ metadata: { ruleName: '', author: '' } })),
    );
    expect(invalid.result.current.isValidForPreview()).toBe(false);
  });

  it('canAddString requires both identifier and value to be non-blank', () => {
    const empty = renderHook(() => useYaraRuleActions(fakeRuleState()));
    expect(empty.result.current.canAddString()).toBe(false);

    const filled = renderHook(() =>
      useYaraRuleActions(
        fakeRuleState({ currentString: { identifier: 'a', type: 'text', value: 'x', modifiers: [] } }),
      ),
    );
    expect(filled.result.current.canAddString()).toBe(true);
  });

  it('canAddTag rejects a blank or already-used tag', () => {
    const blank = renderHook(() => useYaraRuleActions(fakeRuleState({ currentTag: '  ' })));
    expect(blank.result.current.canAddTag()).toBe(false);

    const duplicate = renderHook(() =>
      useYaraRuleActions(fakeRuleState({ currentTag: 'malware', tags: [{ value: 'malware' }] })),
    );
    expect(duplicate.result.current.canAddTag()).toBe(false);

    const novel = renderHook(() =>
      useYaraRuleActions(fakeRuleState({ currentTag: 'new-tag', tags: [{ value: 'malware' }] })),
    );
    expect(novel.result.current.canAddTag()).toBe(true);
  });
});

describe('useYaraRuleActions — clearError', () => {
  it('removes only the named error field', () => {
    const ruleState = fakeRuleState({
      currentString: { identifier: '1bad', type: 'text', value: '', modifiers: [] },
    });
    const { result } = renderHook(() => useYaraRuleActions(ruleState));
    act(() => result.current.handleAddString());
    expect(result.current.errors.identifier).toBeTruthy();

    act(() => result.current.clearError('identifier'));

    expect(result.current.errors.identifier).toBeUndefined();
  });
});

describe('useYaraRuleActions — handleReset', () => {
  it('resets only after confirmation', () => {
    const ruleState = fakeRuleState();
    const { result } = renderHook(() => useYaraRuleActions(ruleState));

    act(() => result.current.handleReset());
    expect(ruleState.resetAll).not.toHaveBeenCalled();

    act(() => result.current.onConfirmReset());
    expect(ruleState.resetAll).toHaveBeenCalledTimes(1);
  });
});

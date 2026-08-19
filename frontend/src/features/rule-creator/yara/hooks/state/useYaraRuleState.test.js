import { act, renderHook } from '@testing-library/react';
import { useYaraRuleState } from './useYaraRuleState';
import { INITIAL_METADATA, INITIAL_CONDITIONS, INITIAL_STRING } from '../../constants/yaraConstants';

describe('useYaraRuleState — strings', () => {
  it('addString appends a string with a generated id', () => {
    const { result } = renderHook(() => useYaraRuleState());

    act(() => result.current.addString({ identifier: 'a', type: 'text', value: 'evil', modifiers: [] }));

    expect(result.current.strings).toHaveLength(1);
    expect(result.current.strings[0]).toMatchObject({ identifier: 'a', value: 'evil' });
    expect(result.current.strings[0].id).toBeTruthy();
  });

  it('removeString removes only the matching id', () => {
    const { result } = renderHook(() => useYaraRuleState());
    act(() => result.current.addString({ identifier: 'a', type: 'text', value: 'x', modifiers: [] }));
    act(() => result.current.addString({ identifier: 'b', type: 'text', value: 'y', modifiers: [] }));
    const idToRemove = result.current.strings[0].id;

    act(() => result.current.removeString(idToRemove));

    expect(result.current.strings).toHaveLength(1);
    expect(result.current.strings[0].identifier).toBe('b');
  });

  it('resetCurrentString restores the blank template', () => {
    const { result } = renderHook(() => useYaraRuleState());
    act(() => result.current.updateCurrentString('identifier', 'a'));

    act(() => result.current.resetCurrentString());

    expect(result.current.currentString).toEqual(INITIAL_STRING);
  });
});

describe('useYaraRuleState — tags', () => {
  it('addTag trims and appends a tag with a generated id', () => {
    const { result } = renderHook(() => useYaraRuleState());

    act(() => result.current.addTag('  ransomware  '));

    expect(result.current.tags).toHaveLength(1);
    expect(result.current.tags[0].value).toBe('ransomware');
    expect(result.current.tags[0].id).toBeTruthy();
  });

  it('does not add a blank tag', () => {
    const { result } = renderHook(() => useYaraRuleState());

    act(() => result.current.addTag('   '));

    expect(result.current.tags).toHaveLength(0);
  });

  it('does not add a duplicate tag value', () => {
    const { result } = renderHook(() => useYaraRuleState());
    act(() => result.current.addTag('malware'));

    act(() => result.current.addTag('malware'));

    expect(result.current.tags).toHaveLength(1);
  });

  it('removeTag removes only the matching id', () => {
    const { result } = renderHook(() => useYaraRuleState());
    act(() => result.current.addTag('a'));
    act(() => result.current.addTag('b'));
    const idToRemove = result.current.tags[0].id;

    act(() => result.current.removeTag(idToRemove));

    expect(result.current.tags.map((t) => t.value)).toEqual(['b']);
  });
});

describe('useYaraRuleState — conditions', () => {
  it('setStringMatchCondition("all") sets all and clears any', () => {
    const { result } = renderHook(() => useYaraRuleState());
    act(() => result.current.setStringMatchCondition('any'));

    act(() => result.current.setStringMatchCondition('all'));

    expect(result.current.conditions.all).toBe(true);
    expect(result.current.conditions.any).toBe(false);
  });
});

describe('useYaraRuleState — resetAll', () => {
  it('restores metadata, strings, conditions, tags, and the current-string/tag drafts', () => {
    const { result } = renderHook(() => useYaraRuleState());
    act(() => result.current.updateMetadata('ruleName', 'Changed'));
    act(() => result.current.addString({ identifier: 'a', type: 'text', value: 'x', modifiers: [] }));
    act(() => result.current.addTag('tag'));
    act(() => result.current.setStringMatchCondition('any'));

    act(() => result.current.resetAll());

    expect(result.current.metadata).toEqual(INITIAL_METADATA);
    expect(result.current.strings).toEqual([]);
    expect(result.current.tags).toEqual([]);
    expect(result.current.conditions).toEqual(INITIAL_CONDITIONS);
    expect(result.current.currentTag).toBe('');
  });
});

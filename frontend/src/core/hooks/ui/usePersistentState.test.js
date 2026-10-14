import { act, renderHook } from '@testing-library/react';
import { usePersistentState } from './usePersistentState';

beforeEach(() => localStorage.clear());

describe('usePersistentState', () => {
  it('starts from the initial value and persists changes', () => {
    const { result } = renderHook(() => usePersistentState('k', 240));
    expect(result.current[0]).toBe(240);

    act(() => result.current[1](300));

    expect(JSON.parse(localStorage.getItem('k'))).toBe(300);
  });

  it('restores a stored value on the next mount', () => {
    localStorage.setItem('k', JSON.stringify(false));
    const { result } = renderHook(() => usePersistentState('k', true));
    expect(result.current[0]).toBe(false);
  });

  it('falls back to the initial value for invalid or corrupt storage', () => {
    localStorage.setItem('a', JSON.stringify(9999));
    localStorage.setItem('b', '{not json');
    const inRange = (v) => v >= 100 && v <= 500;
    expect(renderHook(() => usePersistentState('a', 240, inRange)).result.current[0]).toBe(240);
    expect(renderHook(() => usePersistentState('b', 240)).result.current[0]).toBe(240);
  });
});

import { act, renderHook } from '@testing-library/react';
import { useErrorAlert } from './useErrorAlert';

describe('useErrorAlert', () => {
  it('starts closed with no message', () => {
    const { result } = renderHook(() => useErrorAlert());
    expect(result.current.errorAlert).toEqual({ open: false, message: '' });
  });

  it('showError opens the alert with the given message', () => {
    const { result } = renderHook(() => useErrorAlert());

    act(() => result.current.showError('Something went wrong'));

    expect(result.current.errorAlert).toEqual({ open: true, message: 'Something went wrong' });
  });

  it('hideError resets to the closed state', () => {
    const { result } = renderHook(() => useErrorAlert());
    act(() => result.current.showError('Oops'));

    act(() => result.current.hideError());

    expect(result.current.errorAlert).toEqual({ open: false, message: '' });
  });
});

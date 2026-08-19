import { act, renderHook } from '@testing-library/react';
import { useConfirmDialog } from './useConfirmDialog';

describe('useConfirmDialog', () => {
  it('starts closed', () => {
    const { result } = renderHook(() => useConfirmDialog());
    expect(result.current.dialogState.open).toBe(false);
  });

  it('requestConfirmation opens the dialog with the given title/message', () => {
    const { result } = renderHook(() => useConfirmDialog());

    act(() => result.current.requestConfirmation('Reset?', 'Are you sure?', vi.fn()));

    expect(result.current.dialogState).toMatchObject({
      open: true,
      title: 'Reset?',
      message: 'Are you sure?',
    });
  });

  it('handleConfirm runs the callback and closes the dialog', () => {
    const onConfirm = vi.fn();
    const { result } = renderHook(() => useConfirmDialog());
    act(() => result.current.requestConfirmation('Reset?', 'Are you sure?', onConfirm));

    act(() => result.current.handleConfirm());

    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(result.current.dialogState.open).toBe(false);
  });

  it('handleCancel closes the dialog without running the callback', () => {
    const onConfirm = vi.fn();
    const { result } = renderHook(() => useConfirmDialog());
    act(() => result.current.requestConfirmation('Reset?', 'Are you sure?', onConfirm));

    act(() => result.current.handleCancel());

    expect(onConfirm).not.toHaveBeenCalled();
    expect(result.current.dialogState.open).toBe(false);
  });

  it('handleConfirm does not throw when no callback was given', () => {
    const { result } = renderHook(() => useConfirmDialog());
    expect(() => act(() => result.current.handleConfirm())).not.toThrow();
  });
});

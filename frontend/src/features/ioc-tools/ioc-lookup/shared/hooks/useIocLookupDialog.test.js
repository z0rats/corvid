import { act, renderHook } from '@testing-library/react';
import { useIocLookupDialog } from './useIocLookupDialog';

describe('useIocLookupDialog', () => {
  it('starts closed with no ioc set', () => {
    const { result } = renderHook(() => useIocLookupDialog());
    expect(result.current).toMatchObject({ open: false, ioc: null, iocType: null });
  });

  it('openDialog sets the ioc/type and opens the dialog', () => {
    const { result } = renderHook(() => useIocLookupDialog());

    act(() => result.current.openDialog('1.2.3.4', 'ip'));

    expect(result.current).toMatchObject({ open: true, ioc: '1.2.3.4', iocType: 'ip' });
  });

  it('closeDialog closes the dialog but keeps the last ioc/type', () => {
    const { result } = renderHook(() => useIocLookupDialog());
    act(() => result.current.openDialog('1.2.3.4', 'ip'));

    act(() => result.current.closeDialog());

    expect(result.current.open).toBe(false);
    expect(result.current.ioc).toBe('1.2.3.4');
  });
});

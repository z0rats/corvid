import { render, screen, fireEvent } from '@testing-library/react';
import ResizeHandle from './ResizeHandle';

function renderHandle(props = {}) {
  const onChange = vi.fn();
  const onPointerDown = vi.fn();
  render(
    <ResizeHandle label="Resize tool panel" value={200} min={160} max={360} onChange={onChange} onPointerDown={onPointerDown} {...props} />,
  );
  return { handle: screen.getByRole('separator', { name: 'Resize tool panel' }), onChange, onPointerDown };
}

describe('ResizeHandle', () => {
  it('exposes the current width as a focusable vertical separator', () => {
    const { handle } = renderHandle();
    expect(handle).toHaveAttribute('aria-orientation', 'vertical');
    expect(handle).toHaveAttribute('aria-valuenow', '200');
    expect(handle).toHaveAttribute('tabindex', '0');
  });

  it('steps the width with the arrow keys', () => {
    const { handle, onChange } = renderHandle();
    fireEvent.keyDown(handle, { key: 'ArrowRight' });
    fireEvent.keyDown(handle, { key: 'ArrowLeft' });
    expect(onChange.mock.calls).toEqual([[216], [184]]);
  });

  it('clamps to the bounds and jumps to them with Home/End', () => {
    const { handle, onChange } = renderHandle({ value: 170 });
    fireEvent.keyDown(handle, { key: 'ArrowLeft' });
    fireEvent.keyDown(handle, { key: 'End' });
    fireEvent.keyDown(handle, { key: 'Home' });
    expect(onChange.mock.calls).toEqual([[160], [360], [160]]);
  });

  it('ignores unrelated keys', () => {
    const { handle, onChange } = renderHandle();
    fireEvent.keyDown(handle, { key: 'a' });
    expect(onChange).not.toHaveBeenCalled();
  });

  it('starts a drag on pointer down', () => {
    const { handle, onPointerDown } = renderHandle();
    fireEvent.pointerDown(handle, { clientX: 10 });
    expect(onPointerDown).toHaveBeenCalled();
  });
});

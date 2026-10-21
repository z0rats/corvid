import { useState } from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import CommitTextField from './CommitTextField';

function Harness({ initial, type, onCommit }) {
  const [value, setValue] = useState(initial);
  return (
    <CommitTextField
      label="Field"
      type={type}
      value={value}
      onCommit={(v) => { onCommit(v); setValue(v); }}
    />
  );
}

const field = () => screen.getByLabelText('Field');

describe('CommitTextField', () => {
  it('does not commit while typing, only on blur', () => {
    const onCommit = vi.fn();
    render(<Harness initial={30} type="number" onCommit={onCommit} />);
    fireEvent.focus(field());
    fireEvent.change(field(), { target: { value: '1' } });
    fireEvent.change(field(), { target: { value: '12' } });
    fireEvent.change(field(), { target: { value: '120' } });
    expect(onCommit).not.toHaveBeenCalled();
    fireEvent.blur(field());
    expect(onCommit).toHaveBeenCalledTimes(1);
    expect(onCommit).toHaveBeenCalledWith(120);
  });

  it('keeps a half-typed decimal and commits the full number', () => {
    // Regression: a controlled number field saving per keystroke turned "0." into 0
    const onCommit = vi.fn();
    render(<Harness initial={1} type="number" onCommit={onCommit} />);
    fireEvent.focus(field());
    fireEvent.change(field(), { target: { value: '0.' } });
    fireEvent.change(field(), { target: { value: '0.5' } });
    fireEvent.keyDown(field(), { key: 'Enter' });
    expect(onCommit).toHaveBeenCalledWith(0.5);
  });

  it('an emptied number reverts to the saved value instead of saving 0', () => {
    const onCommit = vi.fn();
    render(<Harness initial={30} type="number" onCommit={onCommit} />);
    fireEvent.focus(field());
    fireEvent.change(field(), { target: { value: '' } });
    fireEvent.blur(field());
    expect(onCommit).not.toHaveBeenCalled();
    expect(field()).toHaveValue(30);
  });

  it('unchanged values are not re-saved; text fields commit strings', () => {
    const onCommit = vi.fn();
    render(<Harness initial="socks5://a" onCommit={onCommit} />);
    fireEvent.focus(field());
    fireEvent.blur(field());
    expect(onCommit).not.toHaveBeenCalled();
    fireEvent.focus(field());
    fireEvent.change(field(), { target: { value: 'socks5://b' } });
    fireEvent.keyDown(field(), { key: 'Enter' });
    expect(onCommit).toHaveBeenCalledWith('socks5://b');
  });

  it('follows an external value change while not focused', () => {
    const { rerender } = render(<CommitTextField label="Field" value="a" onCommit={() => {}} />);
    rerender(<CommitTextField label="Field" value="b" onCommit={() => {}} />);
    expect(field()).toHaveValue('b');
  });
});

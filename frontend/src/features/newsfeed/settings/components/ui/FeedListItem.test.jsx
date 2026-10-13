import { render, screen, fireEvent, within } from '@testing-library/react';
import FeedListItem from './FeedListItem';

const renderItem = (feed, onReliabilityChange = vi.fn()) => {
  render(
    <ul>
      <FeedListItem
        name="Krebs"
        feed={{ url: 'https://k.example/rss', enabled: true, icon: 'default.png', ...feed }}
        onToggle={vi.fn()}
        onReliabilityChange={onReliabilityChange}
        onDelete={vi.fn()}
        onIconDelete={vi.fn()}
        onRefetchIcon={vi.fn()}
      />
    </ul>,
  );
  return onReliabilityChange;
};

describe('FeedListItem reliability', () => {
  it('shows "Not rated" until a grade is set', () => {
    renderItem({});
    expect(screen.getByRole('combobox', { name: 'Reliability' })).toHaveTextContent('Not rated');
  });

  it('shows the current grade', () => {
    renderItem({ reliability: 'C' });
    expect(screen.getByRole('combobox', { name: 'Reliability' })).toHaveTextContent('C');
  });

  it('reports the chosen grade for this feed', () => {
    const onChange = renderItem({});

    fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Reliability' }));
    fireEvent.click(within(screen.getByRole('listbox')).getByText('B — Usually reliable'));

    expect(onChange).toHaveBeenCalledWith('Krebs', 'B');
  });
});

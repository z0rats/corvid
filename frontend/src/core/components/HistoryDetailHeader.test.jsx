import { render, screen } from '@testing-library/react';
import HistoryDetailHeader from './HistoryDetailHeader';

vi.mock('./AddToInvestigationButton', () => ({
  default: ({ feature, runId }) => <button type="button">add {feature} {runId}</button>,
}));

describe('HistoryDetailHeader', () => {
  it('offers "Add to investigation" only when given a run reference', () => {
    const { rerender } = render(<HistoryDetailHeader onBack={() => {}} title="jdoe" />);
    expect(screen.queryByRole('button', { name: /add/ })).not.toBeInTheDocument();

    rerender(<HistoryDetailHeader onBack={() => {}} title="jdoe" runRef={{ feature: 'reddit_search', id: 4 }} />);
    expect(screen.getByRole('button', { name: 'add reddit_search 4' })).toBeInTheDocument();
  });

  it('keeps JSON/CSV export alongside it', () => {
    render(
      <HistoryDetailHeader
        onBack={() => {}}
        title="jdoe"
        exportName="x"
        exportData={{}}
        csvRows={[{ a: 1 }]}
        runRef={{ feature: 'ioc_lookup', id: 1 }}
      />,
    );
    expect(screen.getByRole('button', { name: 'JSON' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'CSV' })).toBeInTheDocument();
  });
});

import { render, screen } from '@testing-library/react';
import CheaterReportCard from './CheaterReportCard';

const REPORT = {
  probability: 0.72,
  level: 'high',
  coverage: 0.8,
  already_banned: true,
  signals: [
    { id: 'own_vac_or_game_ban', value: 1.0, weight: 3.0, contribution: 3.0, explanation: '1 ban(s) on record, most recent 10 days ago' },
    { id: 'accusatory_comments', value: null, weight: 1.5, contribution: 0.0, explanation: 'Not enough comments to evaluate' },
  ],
};

describe('CheaterReportCard', () => {
  it('shows the level and probability', () => {
    render(<CheaterReportCard cheaterReport={REPORT} />);
    expect(screen.getByText(/high - 72%/i)).toBeInTheDocument();
  });

  it('shows the disclaimer that this is a heuristic, not a verdict', () => {
    render(<CheaterReportCard cheaterReport={REPORT} />);
    expect(screen.getByText(/not a verdict or proof of cheating/i)).toBeInTheDocument();
  });

  it('shows an already-banned alert when the account already has a ban', () => {
    render(<CheaterReportCard cheaterReport={REPORT} />);
    expect(screen.getByText(/already has a vac or game ban/i)).toBeInTheDocument();
  });

  it('omits the already-banned alert when there is no ban', () => {
    render(<CheaterReportCard cheaterReport={{ ...REPORT, already_banned: false }} />);
    expect(screen.queryByText(/already has a vac or game ban/i)).not.toBeInTheDocument();
  });

  it('shows the data-coverage line', () => {
    render(<CheaterReportCard cheaterReport={REPORT} />);
    expect(screen.getByText(/80% of signals had usable data/i)).toBeInTheDocument();
  });

  it('renders every signal with its explanation, including ones with no data', () => {
    render(<CheaterReportCard cheaterReport={REPORT} />);

    expect(screen.getByText('Own VAC/game ban')).toBeInTheDocument();
    expect(screen.getByText('1 ban(s) on record, most recent 10 days ago')).toBeInTheDocument();
    expect(screen.getByText('Accusatory comments')).toBeInTheDocument();
    expect(screen.getByText('Not enough comments to evaluate')).toBeInTheDocument();
  });
});

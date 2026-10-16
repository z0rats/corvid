import { render, screen } from '@testing-library/react';
import TextSignalsSection from './TextSignalsSection';

const signal = (overrides) => ({
  kind: 'phone',
  matched: '+381',
  source_text: '+381 11 323 4567',
  countries: ['RS'],
  languages: [],
  strength: 'strong',
  note: null,
  ...overrides,
});

describe('TextSignalsSection', () => {
  it('renders nothing when there is neither text nor a hint', () => {
    const { container } = render(<TextSignalsSection signals={[]} visibleText={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('shows the transcription the hints were derived from', () => {
    render(<TextSignalsSection signals={[signal()]} visibleText={['ПЕКАРА', '+381 11 323 4567']} />);
    expect(screen.getByText('Text read from the photo')).toBeInTheDocument();
    expect(screen.getByText('ПЕКАРА')).toBeInTheDocument();
  });

  it('names countries and languages instead of showing raw codes', () => {
    render(
      <TextSignalsSection
        signals={[
          signal(),
          signal({ kind: 'letter', matched: 'ђ', countries: [], languages: ['sr'], strength: 'medium' }),
        ]}
      />,
    );
    expect(screen.getByText('→ Serbia')).toBeInTheDocument();
    expect(screen.getByText('→ Serbian')).toBeInTheDocument();
    expect(screen.getByText('Letter: ђ')).toBeInTheDocument();
  });

  it('caps long country lists and reports how many were left out', () => {
    render(
      <TextSignalsSection
        signals={[
          signal({
            kind: 'script',
            matched: 'Cyrillic',
            countries: ['RU', 'UA', 'BY', 'BG', 'RS', 'MK'],
            strength: 'medium',
          }),
        ]}
      />,
    );
    expect(screen.getByText(/\+2 more/)).toBeInTheDocument();
    expect(screen.queryByText(/North Macedonia/)).not.toBeInTheDocument();
  });

  it('falls back to the raw kind for a kind the UI does not know', () => {
    render(<TextSignalsSection signals={[signal({ kind: 'plate', matched: 'AB' })]} />);
    expect(screen.getByText('plate: AB')).toBeInTheDocument();
  });
});

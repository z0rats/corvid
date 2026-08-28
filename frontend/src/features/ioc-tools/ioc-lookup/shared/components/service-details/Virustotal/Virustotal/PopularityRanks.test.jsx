import React from 'react';
import { render, screen } from '@testing-library/react';
import PopularityRanks from './PopularityRanks';

describe('PopularityRanks', () => {
  it('renders a card for each popularity source', () => {
    render(
      <PopularityRanks
        result={{
          data: {
            attributes: {
              popularity_ranks: {
                Alexa: { rank: 1000 },
                Statvoo: { rank: 5000 },
              },
            },
          },
        }}
      />
    );

    expect(screen.getByText('Popularity ranks')).toBeInTheDocument();
    expect(screen.getByText('Alexa')).toBeInTheDocument();
    expect(screen.getByText('1000')).toBeInTheDocument();
    expect(screen.getByText('Statvoo')).toBeInTheDocument();
    expect(screen.getByText('5000')).toBeInTheDocument();
  });
});

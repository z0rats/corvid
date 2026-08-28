import React from 'react';
import { render, screen } from '@testing-library/react';
import LeakixDetails from './LeakixDetails';

describe('LeakixDetails', () => {
  it('shows a loading message when result is missing', () => {
    render(<LeakixDetails result={null} ioc="1.2.3.4" />);
    expect(screen.getByText('Loading LeakIX details...')).toBeInTheDocument();
  });

  it('shows an error message when the result carries an error', () => {
    render(<LeakixDetails result={{ error: true, message: 'timeout' }} ioc="1.2.3.4" />);
    expect(screen.getByText('Error fetching LeakIX details: timeout')).toBeInTheDocument();
  });

  it('shows a no-info message when there are no services or leaks', () => {
    render(<LeakixDetails result={{ Services: [], Leaks: [] }} ioc="1.2.3.4" />);
    expect(
      screen.getByText('No services or leaks found on "1.2.3.4" via LeakIX.')
    ).toBeInTheDocument();
  });

  it('lists found leaks under an expanded section by default', () => {
    render(
      <LeakixDetails
        result={{
          Leaks: [{ type: 'mongodb', plugin: 'MongoPlugin', port: 27017, dataset: { rows: 10, databases: 2 } }],
          Services: [],
        }}
        ioc="1.2.3.4"
      />
    );

    expect(screen.getByText('Leaks (1)')).toBeInTheDocument();
    expect(screen.getByText('mongodb')).toBeInTheDocument();
    expect(screen.getByText('MongoPlugin')).toBeInTheDocument();
    expect(screen.getByText(':27017')).toBeInTheDocument();
    expect(screen.getByText('10 row(s) across 2 database(s)')).toBeInTheDocument();
  });

  it('lists found services, collapsed by default', () => {
    render(
      <LeakixDetails
        result={{
          Leaks: [],
          Services: [{ type: 'http', port: 8080, software: { name: 'nginx', version: '1.2' }, hostname: 'host.example' }],
        }}
        ioc="1.2.3.4"
      />
    );

    expect(screen.getByText('Open Services (1)')).toBeInTheDocument();
  });
});

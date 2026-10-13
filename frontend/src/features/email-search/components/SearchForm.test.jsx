import { render, screen, fireEvent } from '@testing-library/react';
import { useState } from 'react';
import SearchForm from './SearchForm';

function Harness({ onSearch, initialSource = 'mailcat' }) {
  const [source, setSource] = useState(initialSource);
  return <SearchForm onSearch={onSearch} source={source} onSourceChange={setSource} />;
}

const box = (label) => screen.getByLabelText(label);
const searchButton = () => screen.getByRole('button', { name: 'Search' });

describe('SearchForm sources', () => {
  it('defaults to mailcat and searches a username with that source', () => {
    const onSearch = vi.fn();
    render(<Harness onSearch={onSearch} />);

    fireEvent.change(box('Username'), { target: { value: 'johndoe' } });
    fireEvent.click(searchButton());

    expect(onSearch).toHaveBeenCalledWith('johndoe', 'mailcat');
  });

  it('switches to a full-email input for user_scanner and passes that source', () => {
    const onSearch = vi.fn();
    render(<Harness onSearch={onSearch} />);

    fireEvent.click(screen.getByText('User Scanner'));
    fireEvent.change(box('Email address'), { target: { value: 'john@example.com' } });
    fireEvent.click(searchButton());

    expect(onSearch).toHaveBeenCalledWith('john@example.com', 'user_scanner');
  });

  it('refuses a bare username for user_scanner and says why', () => {
    const onSearch = vi.fn();
    render(<Harness onSearch={onSearch} initialSource="user_scanner" />);

    fireEvent.change(box('Email address'), { target: { value: 'johndoe' } });

    expect(screen.getByText('This source needs a full email address')).toBeTruthy();
    expect(searchButton().disabled).toBe(true);
    fireEvent.submit(searchButton().closest('form'));
    expect(onSearch).not.toHaveBeenCalled();
  });
});

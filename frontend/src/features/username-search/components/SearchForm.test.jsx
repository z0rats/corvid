import { render, screen, fireEvent } from '@testing-library/react';
import SearchForm from './SearchForm';
import { usernameSearchApi } from '../services/api/usernameSearchApi';

vi.mock('../services/api/usernameSearchApi', () => ({
  usernameSearchApi: { getTags: vi.fn() },
}));

const type = (value) => fireEvent.change(screen.getByLabelText('Username'), { target: { value } });
const searchButton = () => screen.getByRole('button', { name: 'Search' });

beforeEach(() => usernameSearchApi.getTags.mockResolvedValue([]));
afterEach(() => vi.clearAllMocks());

describe('SearchForm pattern mode', () => {
  it('lists the handles a pattern expands to and blocks searching the raw pattern', () => {
    const onSearch = vi.fn();
    render(<SearchForm onSearch={onSearch} />);

    type('john[a-c]');

    expect(screen.getByText('Pattern matches 3 handle(s) — Click to put it in the box, then search')).toBeTruthy();
    ['johna', 'johnb', 'johnc'].forEach((handle) => expect(screen.getByText(handle)).toBeTruthy());
    expect(searchButton().disabled).toBe(true);
    fireEvent.submit(searchButton().closest('form'));
    expect(onSearch).not.toHaveBeenCalled();
  });

  it('puts a picked candidate in the box, ending pattern mode so it can be searched', () => {
    const onSearch = vi.fn();
    render(<SearchForm onSearch={onSearch} />);
    type('john[a-c]');

    fireEvent.click(screen.getByText('johnb'));

    expect(screen.getByLabelText('Username').value).toBe('johnb');
    expect(searchButton().disabled).toBe(false);
    fireEvent.click(searchButton());
    expect(onSearch).toHaveBeenCalledWith('johnb', expect.anything());
  });

  it('says when only the first candidates are shown', () => {
    render(<SearchForm onSearch={() => {}} />);

    type('u[0-9]{0-3}');

    expect(screen.getByText(/Pattern matches 1111 handles, showing the first 100/)).toBeTruthy();
  });

  it('explains a pattern that is too broad or malformed', () => {
    render(<SearchForm onSearch={() => {}} />);

    type('[a-z]{5}');
    expect(screen.getByRole('alert').textContent).toContain('more than 10000');

    type('john[abc');
    expect(screen.getByRole('alert').textContent).toContain('missing "]"');
    expect(searchButton().disabled).toBe(true);
  });

  it('leaves ordinary handles on the heuristic suggestions', () => {
    render(<SearchForm onSearch={() => {}} />);

    type('johnsmith');

    expect(screen.queryByText(/Pattern matches/)).toBeNull();
    expect(screen.getByText('johnsmith1')).toBeTruthy();
    expect(searchButton().disabled).toBe(false);
  });
});

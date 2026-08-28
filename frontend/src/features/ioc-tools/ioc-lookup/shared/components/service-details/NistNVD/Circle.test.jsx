import React from 'react';
import { render } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { lightTheme } from '../../../../../../../core/config/theme';
import Circle from './Circle';

// Reads theme.palette.chart, a custom token this app's theme adds on top of MUI's
// defaults - render through the real theme rather than MUI's bare default.
function renderWithTheme(ui) {
  return render(<ThemeProvider theme={lightTheme}>{ui}</ThemeProvider>);
}

// recharts' ResponsiveContainer measures its real DOM size before mounting its
// chart children, which jsdom always reports as 0x0 - so the value text inside
// the donut never actually reaches the DOM here. This only guards against the
// three severity-band color branches throwing (getFillColor's default/undefined
// case would render a chart with no `fill`, not an error, so this is a smoke test).
describe('Circle', () => {
  it('renders without crashing for a low-band score', () => {
    expect(() => renderWithTheme(<Circle value={2.5} />)).not.toThrow();
  });

  it('renders without crashing for a mid-band score', () => {
    expect(() => renderWithTheme(<Circle value={5} />)).not.toThrow();
  });

  it('renders without crashing for a high-band score', () => {
    expect(() => renderWithTheme(<Circle value={9.8} />)).not.toThrow();
  });
});

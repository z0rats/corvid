import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { lightTheme } from '../../../../../../../../core/config/theme';
import ELFInformation from './ELFInformation';

function renderWithTheme(ui) {
  return render(<ThemeProvider theme={lightTheme}>{ui}</ThemeProvider>);
}

describe('ELFInformation', () => {
  it('renders the header, section list, and segment list', () => {
    renderWithTheme(
      <ELFInformation
        result={{
          data: {
            attributes: {
              elf_info: {
                header: { type: 'EXEC', machine: 'x86-64' },
                section_list: [
                  {
                    name: '.text',
                    section_type: 'PROGBITS',
                    virtual_address: '0x1000',
                    physical_offset: '0x1000',
                    flags: 'AX',
                    size: '2048',
                  },
                ],
                segment_list: [{ segment_type: 'LOAD', resources: ['.text', '.data'] }],
              },
            },
          },
        }}
      />
    );

    expect(
      screen.getByText('ELF information (Executable and Linkable Format)')
    ).toBeInTheDocument();
    expect(screen.getByText('type')).toBeInTheDocument();
    expect(screen.getByText('EXEC')).toBeInTheDocument();
    expect(screen.getByText('.text')).toBeInTheDocument();
    expect(screen.getByText('PROGBITS')).toBeInTheDocument();
    expect(screen.getByText('LOAD')).toBeInTheDocument();
    expect(screen.getByText('.text, .data')).toBeInTheDocument();
  });
});

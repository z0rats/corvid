import React from 'react';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableRow from '@mui/material/TableRow';

// Label/value rows for a provider card; a row whose value is null, undefined or '' is skipped,
// so a source that omits a field shows nothing rather than an empty line.
export default function FieldTable({ rows, label }) {
  const visible = rows.filter(({ value }) => value !== null && value !== undefined && value !== '');
  if (visible.length === 0) return null;
  return (
    <Table size="small" aria-label={label}>
      <TableBody>
        {visible.map(({ key, name, value }) => (
          <TableRow key={key || name}>
            <TableCell component="th" scope="row" sx={{ width: '35%', color: 'text.secondary' }}>
              {name}
            </TableCell>
            <TableCell>{value}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

import React, { useState } from 'react';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';
import RouteIcon from '@mui/icons-material/Route';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

const HOP_COLUMNS = [
  { key: 'number', label: 'Hop' },
  { key: 'from', label: 'From', monospace: true },
  { key: 'by', label: 'By', monospace: true },
  { key: 'with', label: 'With' },
  { key: 'date', label: 'Date / Time' },
];

export default function Hops({ result }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <Accordion
      expanded={expanded}
      onChange={() => setExpanded(!expanded)}
      sx={{ mt: 2 }}
    >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        aria-controls="hops-content"
        id="hops-header"
        sx={{ minHeight: '48px', padding: '0 16px' }}
      >
        <Box display="flex" alignItems="center">
          <RouteIcon sx={{ mr: 1 }} fontSize="small" />
          <Typography variant="subtitle1" fontWeight="medium">
            Hops ({result ? result.length : 0})
          </Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ p: 1 }}>
        {result ? (
          <TableContainer component={Paper} sx={{ maxWidth: '100%', boxShadow: 0, borderRadius: 1 }}>
            <Table size="small" aria-label="hops table">
              <TableHead>
                <TableRow>
                  {HOP_COLUMNS.map(({ key, label }) => (
                    <TableCell key={key} align="left" sx={{ py: 1 }}>
                      <Typography variant="body2" fontWeight="medium">{label}</Typography>
                    </TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {result.map((row, index) => (
                  <TableRow key={`${row.number}-${row.from}-${row.by}`} sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
                    {HOP_COLUMNS.map(({ key, monospace }) => (
                      <TableCell key={key} align="left" sx={{ overflowWrap: 'anywhere', py: 0.75 }}>
                        <Typography
                          variant="body2"
                          {...(monospace && { fontFamily: 'monospace', fontSize: '0.8125rem' })}
                        >
                          {row[key]}
                        </Typography>
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Typography variant="body2" sx={{ px: 1 }}>
            Could not parse hops
          </Typography>
        )}
      </AccordionDetails>
    </Accordion>
  );
}

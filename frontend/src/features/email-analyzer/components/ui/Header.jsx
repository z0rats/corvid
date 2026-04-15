import React, { useState, useMemo } from 'react';
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
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import HorizontalSplitIcon from '@mui/icons-material/HorizontalSplit';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import SearchIcon from '@mui/icons-material/Search';
import InputAdornment from '@mui/material/InputAdornment';

export default function Header({ result }) {
  const [expanded, setExpanded] = useState(false);
  const [filterText, setFilterText] = useState('');

  const filteredHeaders = useMemo(() => {
    if (!result || !filterText) return result ? Object.entries(result) : [];
    const query = filterText.toLowerCase();
    return Object.entries(result).filter(([, entry]) => {
      const key = String(Object.keys(entry)).toLowerCase();
      const value = String(Object.values(entry)).toLowerCase();
      return key.includes(query) || value.includes(query);
    });
  }, [result, filterText]);

  return (
    <Accordion
      expanded={expanded}
      onChange={() => setExpanded(!expanded)}
      sx={{ mt: 2 }}
    >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        aria-controls="header-fields-content"
        id="header-fields-header"
        sx={{ minHeight: '48px', padding: '0 16px' }}
      >
        <Box display="flex" alignItems="center">
          <HorizontalSplitIcon sx={{ mr: 1 }} fontSize="small" />
          <Typography variant="subtitle1" fontWeight="medium">
            Complete Header ({result ? result.length : 0} fields)
          </Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ p: 1 }}>
        {result ? (
          <>
            <TextField
              size="small"
              placeholder="Filter headers..."
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              fullWidth
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon fontSize="small" />
                    </InputAdornment>
                  ),
                },
              }}
              sx={{ mb: 1 }}
            />
            <TableContainer
              component={Paper}
              sx={{ maxWidth: '100%', maxHeight: 400, overflow: 'auto', boxShadow: 0, borderRadius: 1 }}
            >
              <Table size="small" stickyHeader aria-label="header fields table">
                <TableHead>
                  <TableRow>
                    <TableCell align="left" sx={{ py: 1, width: '30%' }}>
                      <Typography variant="body2" fontWeight="medium">Key</Typography>
                    </TableCell>
                    <TableCell align="left" sx={{ py: 1 }}>
                      <Typography variant="body2" fontWeight="medium">Value</Typography>
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredHeaders.map(([, entry], index) => (
                    <TableRow key={`${String(Object.keys(entry))}-${index}`} sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
                      <TableCell align="left" sx={{ py: 0.75 }}>
                        <Typography variant="body2" fontWeight="medium">{Object.keys(entry)}</Typography>
                      </TableCell>
                      <TableCell align="left" sx={{ overflowWrap: 'anywhere', py: 0.75 }}>
                        <Typography variant="body2" fontFamily="monospace" fontSize="0.8125rem">
                          {Object.values(entry)}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            {filterText && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                Showing {filteredHeaders.length} of {result.length} fields
              </Typography>
            )}
          </>
        ) : (
          <Typography variant="body2" sx={{ px: 1 }}>
            No header fields available
          </Typography>
        )}
      </AccordionDetails>
    </Accordion>
  );
}

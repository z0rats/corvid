import React from 'react';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Pagination from '@mui/material/Pagination';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import { processSourcesForDisplay } from './utils/mandiantDataUtils';

const ROWS_PER_PAGE = 10;

export default function MandiantIndicators({ indicators, page, onPageChange }) {
  const paginatedIndicators = indicators.slice((page - 1) * ROWS_PER_PAGE, page * ROWS_PER_PAGE);
  const chunkedIndicators = [];
  for (let i = 0; i < paginatedIndicators.length; i += 2) {
    chunkedIndicators.push(paginatedIndicators.slice(i, i + 2));
  }

  return (
    <Box>
      {chunkedIndicators.map((row, rowIndex) => (
        <Grid container spacing={2} key={`row-${row.map(i => i.value).join('-')}`} sx={{ mb: 2 }}>
          {row.map((indicator) => {
            const processedSources = processSourcesForDisplay(indicator.sources);
            return (
              <Grid size={{ xs: 12, md: 6 }} key={indicator.value}>
                <Box sx={{ p: 2, backgroundColor: (t) => t.palette.mode === 'dark' ? t.palette.background.default : t.palette.grey[100], height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <Typography variant="subtitle1" fontWeight="bold">{indicator.value}</Typography>
                  <Typography variant="body2" color="text.secondary">Type: {indicator.type}</Typography>
                  <Box display="flex" alignItems="center" mt={1}>
                    <Typography variant="body2" mr={1}>Risk Score:</Typography>
                    <Box sx={{ backgroundColor: indicator.mscore < 20 ? 'success.main' : indicator.mscore < 40 ? 'warning.main' : 'error.main', px: 1, py: 0.5, borderRadius: 1, display: 'inline-block', color: 'white' }}>
                      {indicator.mscore}
                    </Box>
                  </Box>
                  <Box mt={1}>
                    <Typography variant="body2">First seen: {indicator.first_seen ? new Date(indicator.first_seen).toLocaleDateString() : 'N/A'}</Typography>
                    <Typography variant="body2">Last seen: {indicator.last_seen ? new Date(indicator.last_seen).toLocaleDateString() : 'N/A'}</Typography>
                  </Box>
                  <Box mt={2} sx={{ flexGrow: 1 }}>
                    {processedSources.length > 0 && (
                      <>
                        <Typography variant="body2" fontWeight="bold">Sources:</Typography>
                        <Box mt={1}>
                          {processedSources.map((source) => (
                            <Box key={source.source_name} sx={{ mb: 1 }}>
                              <Typography variant="body2">{source.source_name}</Typography>
                              {source.category && source.category.length > 0 && (
                                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                                  {source.category.map((cat) => (
                                    <Chip
                                      key={cat}
                                      label={cat}
                                      size="small"
                                      color={cat.includes('malware') ? 'error' : cat.includes('control') ? 'warning' : 'info'}
                                      sx={{ mr: 0.5, mb: 0.5 }}
                                    />
                                  ))}
                                </Box>
                              )}
                            </Box>
                          ))}
                        </Box>
                      </>
                    )}
                  </Box>
                </Box>
              </Grid>
            );
          })}
        </Grid>
      ))}
      {indicators.length > ROWS_PER_PAGE && (
        <Box display="flex" justifyContent="center" mt={2}>
          <Pagination
            count={Math.ceil(indicators.length / ROWS_PER_PAGE)}
            page={page}
            onChange={onPageChange}
            color="primary"
          />
        </Box>
      )}
    </Box>
  );
}

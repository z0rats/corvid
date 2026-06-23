import React from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Pagination from '@mui/material/Pagination';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import CategoryIcon from '@mui/icons-material/Category';

const ROWS_PER_PAGE = 10;

function openReportInNewTab(reportId) {
  window.open(`https://advantage.mandiant.com/reports/${reportId}`, '_blank', 'noopener,noreferrer');
}

export default function MandiantReports({ reports, page, onPageChange }) {
  const paginatedReports = reports.slice((page - 1) * ROWS_PER_PAGE, page * ROWS_PER_PAGE);
  const chunkedReports = [];
  for (let i = 0; i < paginatedReports.length; i += 2) {
    chunkedReports.push(paginatedReports.slice(i, i + 2));
  }

  return (
    <Box>
      {chunkedReports.map((row, rowIndex) => (
        <Grid container spacing={2} key={rowIndex} sx={{ mb: 2 }}>
          {row.map((report, colIndex) => (
            <Grid size={{ xs: 12, md: 6 }} key={colIndex}>
              <Box sx={{ p: 2, backgroundColor: (t) => t.palette.mode === 'dark' ? t.palette.background.default : t.palette.grey[100], height: '100%', display: 'flex', flexDirection: 'column' }}>
                <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                  <Typography variant="subtitle1" fontWeight="bold" sx={{ flexGrow: 1, mr: 2 }}>
                    {report.title}
                  </Typography>
                  <Button
                    variant="outlined"
                    size="small"
                    color="primary"
                    startIcon={<OpenInNewIcon />}
                    onClick={() => openReportInNewTab(report.report_id)}
                    sx={{ minWidth: 'auto', whiteSpace: 'nowrap' }}
                  >
                    Open
                  </Button>
                </Box>
                <Box mt={1} display="flex" alignItems="center">
                  <CalendarTodayIcon fontSize="small" sx={{ mr: 1 }} />
                  <Typography variant="body2">
                    Published: {new Date(report.publish_date).toLocaleDateString()}
                  </Typography>
                </Box>
                <Box mt={1} display="flex" flexWrap="wrap" alignItems="flex-start">
                  <Box display="flex" alignItems="center" sx={{ mr: 1 }}>
                    <CategoryIcon fontSize="small" sx={{ mr: 1 }} />
                    <Typography variant="body2">Type: {report.report_type || 'N/A'}</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                    {report.threat_scape?.map((scope, i) => (
                      <Chip key={i} label={scope} size="small" color="primary" sx={{ mr: 0.5, mb: 0.5 }} />
                    ))}
                  </Box>
                </Box>
                <Box mt={1} sx={{ flexGrow: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    Report ID: {report.report_id}
                  </Typography>
                </Box>
              </Box>
            </Grid>
          ))}
        </Grid>
      ))}
      {reports.length > ROWS_PER_PAGE && (
        <Box display="flex" justifyContent="center" mt={2}>
          <Pagination
            count={Math.ceil(reports.length / ROWS_PER_PAGE)}
            page={page}
            onChange={onPageChange}
            color="primary"
          />
        </Box>
      )}
    </Box>
  );
}

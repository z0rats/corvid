import React, { useState } from 'react';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TablePagination from '@mui/material/TablePagination';
import TableRow from '@mui/material/TableRow';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import AppSnackbar from '../../../../../core/components/ui/AppSnackbar';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import NoData from './NoData';
import AnalysisModal from './AnalysisModal';
import { copyIOCsToClipboard, exportIOCsToFile } from '../../utils/iocExportUtils';

const iocCellSx = { py: 1, wordBreak: 'break-all', fontSize: '0.875rem' };
const actionsCellSx = { py: 1 };
const analyzeButtonSx = { minWidth: 'auto', px: 1.5, py: 0.25, fontSize: '0.75rem' };

export default function ResultRows({ title, type, list = [], count, icon }) {
  const [selectedIoc, setSelectedIoc] = useState(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  const startIndex = page * rowsPerPage;
  const paginatedList = list.slice(startIndex, startIndex + rowsPerPage);
  const sanitizedTitle = title.toLowerCase();

  const handleCopyAll = async () => {
    try {
      const result = await copyIOCsToClipboard(list);
      setSnackbar({ open: true, message: result.message, severity: 'success' });
    } catch {
      setSnackbar({ open: true, message: 'Failed to copy to clipboard', severity: 'error' });
    }
  };

  const handleExportAll = () => {
    try {
      const filename = sanitizedTitle.replace(/\s+/g, '_');
      const result = exportIOCsToFile(list, filename);
      setSnackbar({ open: true, message: result.message, severity: 'success' });
    } catch {
      setSnackbar({ open: true, message: 'Failed to export to file', severity: 'error' });
    }
  };

  return (
    <>
      <Accordion sx={{ boxShadow: 1, '&:before': { display: 'none' } }}>
        <AccordionSummary
          expandIcon={<ExpandMoreIcon />}
          aria-controls={`${type}-content`}
          id={`${type}-header`}
          sx={{ minHeight: 48, '&.Mui-expanded': { minHeight: 48 } }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', pr: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              {icon}
              <Typography sx={{ ml: 1, fontWeight: 500 }}>
                {title} ({count})
              </Typography>
            </Box>
            {list.length > 0 && (
              <Box sx={{ display: 'flex', gap: 1 }} onClick={(e) => e.stopPropagation()}>
                <Tooltip title={`Copy all ${sanitizedTitle}`}>
                  <IconButton size="small" onClick={handleCopyAll} aria-label="Copy all">
                    <ContentCopyIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title={`Export all ${sanitizedTitle}`}>
                  <IconButton size="small" onClick={handleExportAll} aria-label="Export all">
                    <FileDownloadIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>
            )}
          </Box>
        </AccordionSummary>
        <AccordionDetails sx={{ p: 0 }}>
          {list.length > 0 ? (
            <Box>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 600, py: 1 }}>IOC</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600, py: 1, width: 100 }}>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginatedList.map((ioc, index) => (
                    <TableRow key={`${startIndex + index}_${type}`} hover>
                      <TableCell sx={iocCellSx}>
                        {ioc}
                      </TableCell>
                      <TableCell align="right" sx={actionsCellSx}>
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => setSelectedIoc(ioc)}
                          sx={analyzeButtonSx}
                        >
                          Analyze
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              {list.length > rowsPerPage && (
                <TablePagination
                  component="div"
                  count={list.length}
                  page={page}
                  onPageChange={(_, newPage) => setPage(newPage)}
                  rowsPerPage={rowsPerPage}
                  onRowsPerPageChange={(e) => { setRowsPerPage(parseInt(e.target.value, 10)); setPage(0); }}
                  rowsPerPageOptions={[5, 10, 25, 50, 100]}
                  sx={{ borderTop: '1px solid', borderColor: 'divider' }}
                />
              )}
            </Box>
          ) : (
            <Box sx={{ p: 1.5, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
              <NoData />
            </Box>
          )}
        </AccordionDetails>
      </Accordion>

      <AnalysisModal
        open={Boolean(selectedIoc)}
        onClose={() => setSelectedIoc(null)}
        ioc={selectedIoc}
        iocType={type}
      />

      <AppSnackbar
        open={snackbar.open}
        message={snackbar.message}
        severity={snackbar.severity}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      />
    </>
  );
}

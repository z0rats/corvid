import React, { useState } from 'react';
import IocLookupDialog from '../../../ioc-tools/ioc-lookup/shared/components/IocLookupDialog';
import { useIocLookupDialog } from '../../../ioc-tools/ioc-lookup/shared/hooks/useIocLookupDialog';
import { EMAIL_CONSTANTS } from '../../constants/emailConstants';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';
import LinkIcon from '@mui/icons-material/Link';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

export default function Urls({ result }) {
  const [expanded, setExpanded] = useState(false);
  const { open, ioc, iocType, openDialog, closeDialog } = useIocLookupDialog();

  return (
    <Accordion
      expanded={expanded}
      onChange={() => setExpanded(!expanded)}
      sx={{ mt: 2 }}
    >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        aria-controls="urls-content"
        id="urls-header"
        sx={{ minHeight: '48px', padding: '0 16px' }}
      >
        <Box display="flex" alignItems="center">
          <LinkIcon sx={{ mr: 1 }} fontSize="small" />
          <Typography variant="subtitle1" fontWeight="medium">
            URLs in body ({result.length})
          </Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ p: 1 }}>
        {result.length > 0 ? (
          <>
            <TableContainer component={Paper} sx={{ maxWidth: '100%', boxShadow: 0, borderRadius: 1 }}>
              <Table size="small" aria-label="urls table">
                <TableBody>
                  {result.map((url, index) => (
                    <TableRow key={url}>
                      <TableCell
                        align="left"
                        sx={{ overflowWrap: 'anywhere', py: 0.75, fontFamily: 'monospace', fontSize: '0.8125rem' }}
                      >
                        {url}
                      </TableCell>
                      <TableCell sx={{ overflowWrap: 'anywhere', width: '120px', whiteSpace: 'nowrap', py: 0.75 }}>
                        <Button
                          variant="outlined"
                          disableElevation
                          size="small"
                          onClick={() => openDialog(url, EMAIL_CONSTANTS.IOC_TYPES.URL)}
                        >
                          Analyze
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            <IocLookupDialog open={open} onClose={closeDialog} ioc={ioc} iocType={iocType} />
          </>
        ) : (
          <Typography variant="body2" sx={{ px: 1 }}>
            No URLs found
          </Typography>
        )}
      </AccordionDetails>
    </Accordion>
  );
}

import React from 'react';
import Box from '@mui/material/Box';
import Modal from '@mui/material/Modal';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import ResultTable from '../../../ioc-lookup/single-lookup/components/ui/ResultTable';
import { mapIocTypeToLabel } from '../../utils/iocExportUtils';

export default function AnalysisModal({ open, onClose, ioc, iocType }) {
  if (!ioc) return null;

  return (
    <Modal open={open} onClose={onClose}>
      <Box
        sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: '60%',
          overflowY: 'scroll',
          maxHeight: '90%',
          p: 4,
        }}
      >
        <Paper sx={{ p: 2, width: '100%', borderRadius: 5 }}>
          <Stack spacing={2} sx={{ width: '100%' }}>
            <Typography>
              <b>Analysis for: </b>{ioc}
            </Typography>
            <ResultTable ioc={ioc} iocType={mapIocTypeToLabel(iocType)} />
          </Stack>
        </Paper>
      </Box>
    </Modal>
  );
}

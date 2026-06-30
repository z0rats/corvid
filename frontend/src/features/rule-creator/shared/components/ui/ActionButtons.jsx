import React from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import PreviewIcon from '@mui/icons-material/Preview';
import DownloadIcon from '@mui/icons-material/Download';
import DeleteIcon from '@mui/icons-material/Delete';

export default function ActionButtons({
  onPreview,
  onExport,
  onReset,
  canPreview,
  canExport,
  ruleType = 'Rule',
}) {
  const { t } = useTranslation('ruleCreator');
  return (
    <Box display="flex" justifyContent="center" sx={{ mt: 2 }}>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
        <Button
          variant="outlined"
          startIcon={<PreviewIcon />}
          onClick={onPreview}
          disabled={!canPreview}
          size="small"
        >
          {t('common.actions.previewRule')}
        </Button>
        <Button
          variant="contained"
          color="primary"
          startIcon={<DownloadIcon />}
          onClick={onExport}
          disabled={!canExport}
          size="small"
        >
          {t('common.actions.exportRule', { ruleType })}
        </Button>
        <Button
          variant="outlined"
          color="secondary"
          startIcon={<DeleteIcon />}
          onClick={onReset}
          size="small"
        >
          {t('common.actions.reset')}
        </Button>
      </Stack>
    </Box>
  );
}

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import FormControl from '@mui/material/FormControl';
import FormControlLabel from '@mui/material/FormControlLabel';
import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import Typography from '@mui/material/Typography';
import DownloadIcon from '@mui/icons-material/Download';
import { useImageMetadataRemoval } from '../../hooks/api/useImageMetadataRemoval';

export default function RemoveMetadataPanel({ file }) {
  const { t } = useTranslation('imageTools');
  const [mode, setMode] = useState('all');
  const { loading, error, success, removeMetadata } = useImageMetadataRemoval();

  return (
    <Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('removeMetadata.description')}
      </Typography>

      <FormControl sx={{ mb: 2 }}>
        <RadioGroup value={mode} onChange={(e) => setMode(e.target.value)}>
          <FormControlLabel value="all" control={<Radio size="small" />} label={t('removeMetadata.modeAll')} />
          <FormControlLabel value="location_only" control={<Radio size="small" />} label={t('removeMetadata.modeLocationOnly')} />
        </RadioGroup>
      </FormControl>

      <Box>
        <Button
          variant="contained"
          disableElevation
          startIcon={<DownloadIcon />}
          disabled={loading || !file}
          onClick={() => removeMetadata(file, mode)}
        >
          {t('removeMetadata.downloadButton')}
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mt: 2 }}>{t('removeMetadata.success')}</Alert>}
    </Box>
  );
}

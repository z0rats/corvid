import React, { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import LinearProgress from '@mui/material/LinearProgress';
import Typography from '@mui/material/Typography';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import { useImageAnomalies } from '../../hooks/api/useImageAnomalies';

function FindingRow({ finding }) {
  const { t } = useTranslation('imageTools');
  return (
    <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5, py: 1, borderBottom: '1px solid', borderColor: 'divider' }}>
      <WarningAmberIcon color="warning" fontSize="small" sx={{ mt: 0.25 }} />
      <Box>
        <Chip size="small" label={t(`anomalies.checks.${finding.check}`, finding.check)} sx={{ mb: 0.5 }} />
        <Typography variant="body2" color="text.secondary">{finding.message}</Typography>
      </Box>
    </Box>
  );
}

export default function AnomalyPanel({ file }) {
  const { t } = useTranslation('imageTools');
  const { result, loading, error, analyzeAnomalies } = useImageAnomalies();

  useEffect(() => {
    if (file) {
      analyzeAnomalies(file);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [file]);

  return (
    <Box>
      {loading && <LinearProgress sx={{ mb: 2 }} />}
      {error && <Alert severity="error">{error}</Alert>}

      {result && (
        <Box>
          {result.findings.length === 0 ? (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
              <CheckCircleIcon color="success" />
              <Typography variant="subtitle1" fontWeight="medium">{t('anomalies.noneDetected')}</Typography>
            </Box>
          ) : (
            <Box sx={{ mb: 1 }}>
              {result.findings.map((finding) => (
                <FindingRow key={finding.check} finding={finding} />
              ))}
            </Box>
          )}
          <Typography variant="caption" color="text.secondary">
            {t('anomalies.checksRun', { count: result.checks_run })}
          </Typography>
        </Box>
      )}
    </Box>
  );
}

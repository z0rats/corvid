import React, { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import LinearProgress from '@mui/material/LinearProgress';
import Link from '@mui/material/Link';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import VerifiedIcon from '@mui/icons-material/Verified';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import ReportProblemIcon from '@mui/icons-material/ReportProblem';
import HelpOutlineIcon from '@mui/icons-material/HelpOutlined';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { useChronoverify } from '../../hooks/api/useChronoverify';

const VERDICT_META = {
  provenance_confirmed: { color: 'success', Icon: VerifiedIcon },
  consistent: { color: 'success', Icon: CheckCircleIcon },
  metadata_anomaly: { color: 'warning', Icon: WarningAmberIcon },
  manipulation_indicated: { color: 'error', Icon: ReportProblemIcon },
  inconclusive: { color: 'default', Icon: HelpOutlineIcon },
};

function VerdictChip({ verdict, t }) {
  const meta = VERDICT_META[verdict] || VERDICT_META.inconclusive;
  return (
    <Chip
      icon={<meta.Icon fontSize="small" />}
      color={meta.color === 'default' ? undefined : meta.color}
      label={t(`chronoverify.verdicts.${verdict}`, verdict)}
      sx={{ fontWeight: 'medium' }}
    />
  );
}

function DetailRow({ label, value }) {
  if (!value) return null;
  return (
    <Box sx={{ display: 'flex', gap: 1 }}>
      <Typography variant="body2" color="text.secondary" sx={{ minWidth: 120 }}>{label}</Typography>
      <Typography variant="body2">{value}</Typography>
    </Box>
  );
}

export default function ChronoverifyPanel({ file }) {
  const { t } = useTranslation('imageTools');
  const { result, loading, error, checkProvenance, reset } = useChronoverify();

  useEffect(() => {
    reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [file]);

  const deviceLabel = result?.capture_device
    ? [result.capture_device.make, result.capture_device.model].filter(Boolean).join(' ')
    : null;

  const locationLabel = result?.location?.present
    ? [result.location.place, result.location.city, result.location.region, result.location.country]
        .filter(Boolean)
        .join(', ') ||
      (result.location.latitude != null && result.location.longitude != null
        ? `${result.location.latitude}, ${result.location.longitude}`
        : null)
    : null;

  const c2paLabel = result?.c2pa
    ? result.c2pa.validated
      ? t('chronoverify.credentialsValidated')
      : result.c2pa.present
        ? t('chronoverify.credentialsPresentNotValidated')
        : t('chronoverify.credentialsNone')
    : null;

  return (
    <Box>
      <Alert severity="info" variant="outlined" sx={{ mb: 2, borderRadius: 1 }}>
        {t('chronoverify.consentDescription')}{' '}
        <Link href="https://chronoverify.com/method" target="_blank" rel="noopener noreferrer">
          {t('chronoverify.methodLink')}
        </Link>
      </Alert>

      {!result && !loading && (
        <Button
          variant="outlined"
          startIcon={<CloudUploadIcon />}
          onClick={() => file && checkProvenance(file)}
          disabled={!file}
        >
          {t('chronoverify.checkButton')}
        </Button>
      )}

      {loading && <LinearProgress sx={{ mb: 2 }} />}
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {result && (
        <Stack spacing={1.5}>
          <Stack
            direction="row"
            spacing={1.5}
            sx={{
              alignItems: "center",
              flexWrap: "wrap",
              gap: 1
            }}>
            <VerdictChip verdict={result.verdict} t={t} />
            <Typography variant="caption" color="text.secondary">
              {t('chronoverify.confidence', { value: Math.round(result.confidence) })}
            </Typography>
          </Stack>

          <Typography variant="body2">{result.summary}</Typography>

          <Divider />

          <DetailRow label={t('chronoverify.captureTime')} value={result.capture_time} />
          <DetailRow label={t('chronoverify.device')} value={deviceLabel} />
          <DetailRow label={t('chronoverify.location')} value={locationLabel} />
          <DetailRow label={t('chronoverify.contentCredentials')} value={c2paLabel} />
          <DetailRow label={t('chronoverify.fingerprint')} value={result.sha256} />

          {result.signals.length > 0 && (
            <Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                {t('chronoverify.signals')}
              </Typography>
              <Stack spacing={0.5}>
                {result.signals.map((signal) => (
                  <Typography key={signal.name} variant="body2" color="text.secondary">
                    &bull; {signal.detail}
                  </Typography>
                ))}
              </Stack>
            </Box>
          )}

          <Typography variant="caption" color="text.secondary">
            {t('chronoverify.disclaimer')}
          </Typography>

          <Button size="small" onClick={() => checkProvenance(file)} sx={{ alignSelf: 'flex-start' }}>
            {t('chronoverify.recheckButton')}
          </Button>
        </Stack>
      )}
    </Box>
  );
}

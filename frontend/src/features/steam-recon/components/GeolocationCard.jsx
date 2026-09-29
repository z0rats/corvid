import { useTranslation } from 'react-i18next';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import Grid from '@mui/material/Grid';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

import { formatLocation } from '../utils/steamFormat';

const CONFIDENCE_COLOR = { high: 'success', medium: 'warning', low: 'default' };

function CandidateList({ candidates }) {
  if (candidates.length === 0) return <Typography color="text.secondary">-</Typography>;
  return (
    <Stack spacing={0.5}>
      {candidates.map((c) => (
        <Stack key={c.code} direction="row" spacing={1} sx={{ alignItems: 'baseline' }}>
          <Typography variant="body2">{c.name || c.code}</Typography>
          <Typography variant="caption" color="text.secondary">
            {(c.share * 100).toFixed(0)}%
          </Typography>
        </Stack>
      ))}
    </Stack>
  );
}

export default function GeolocationCard({ geolocation }) {
  const { t } = useTranslation('steamRecon');
  const { confidence, num_voters: numVoters, coverage, countries, states, cities, self_declared: selfDeclared } = geolocation;

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mb: 1 }}>
        <Typography variant="h6" component="h2">
          {t('geolocation.title')}
        </Typography>
        <Chip size="small" color={CONFIDENCE_COLOR[confidence] || 'default'} label={t(`geolocation.confidence.${confidence}`)} />
      </Stack>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('geolocation.subtitle')}
      </Typography>

      {countries.length === 0 ? (
        <Typography color="text.secondary">{t('geolocation.noHypothesis')}</Typography>
      ) : (
        <>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, sm: 4 }}>
              <Typography variant="caption" color="text.secondary">
                {t('geolocation.levels.country')}
              </Typography>
              <CandidateList candidates={countries} />
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <Typography variant="caption" color="text.secondary">
                {t('geolocation.levels.state')}
              </Typography>
              <CandidateList candidates={states} />
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <Typography variant="caption" color="text.secondary">
                {t('geolocation.levels.city')}
              </Typography>
              <CandidateList candidates={cities} />
            </Grid>
          </Grid>

          <Divider sx={{ my: 2 }} />
          <Typography variant="body2" color="text.secondary">
            {t('geolocation.coverage', { voters: numVoters, coverage: `${(coverage * 100).toFixed(0)}%` })}
          </Typography>
        </>
      )}

      {selfDeclared && (
        <Typography variant="body2" sx={{ mt: 1 }}>
          {t('geolocation.selfDeclared')}: {formatLocation(selfDeclared)}
        </Typography>
      )}
    </Paper>
  );
}

import { useTranslation } from 'react-i18next';
import { useParams, useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Stack from '@mui/material/Stack';
import LinearProgress from '@mui/material/LinearProgress';
import Button from '@mui/material/Button';
import DownloadIcon from '@mui/icons-material/Download';

import HistoryDetailHeader from '../../../core/components/HistoryDetailHeader';
import { useHistoryDetail } from '../../../core/hooks/useHistoryDetail';
import FoundSitesList from './FoundSitesList';
import { usernameSearchApi } from '../services/api/usernameSearchApi';
import { sourceLabelKey } from '../utils/sourceLabels';

const STATUS_COLORS = { running: 'info', completed: 'success', cancelled: 'warning', failed: 'error' };
const EXPORT_FORMATS = ['csv', 'txt', 'json', 'html', 'pdf', 'xmind'];

export default function HistoryDetail() {
  const { t } = useTranslation('usernameSearch');
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: run, loading } = useHistoryDetail(usernameSearchApi.getRun, id);

  if (loading) return <LinearProgress />;
  if (!run) return <Typography color="text.secondary">{t('history.notFound')}</Typography>;

  return (
    <Box>
      <HistoryDetailHeader
        onBack={() => navigate('/username-search/history')}
        title={run.username}
        chips={(
          <>
            <Chip size="small" variant="outlined" label={t(sourceLabelKey(run.source))} />
            <Chip size="small" label={t(`history.status.${run.status}`)} color={STATUS_COLORS[run.status] || 'default'} />
          </>
        )}
        summary={t('history.summary', { checked: run.total_sites_checked, found: run.found_count })}
        error={run.status === 'failed' ? run.error_message : null}
      />

      {run.tags && run.tags.length > 0 && (
        <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary">{t('history.tagsUsed')}:</Typography>
          {run.tags.map((tag) => <Chip key={tag} size="small" label={tag} variant="outlined" />)}
        </Stack>
      )}

      {run.has_export && (
        <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: 'wrap' }}>
          {EXPORT_FORMATS.map((fmt) => (
            <Button
              key={fmt}
              size="small"
              variant="outlined"
              startIcon={<DownloadIcon />}
              component="a"
              href={usernameSearchApi.exportUrl(run.id, fmt)}
              download
            >
              {fmt.toUpperCase()}
            </Button>
          ))}
        </Stack>
      )}

      <FoundSitesList sites={run.site_results} />
    </Box>
  );
}

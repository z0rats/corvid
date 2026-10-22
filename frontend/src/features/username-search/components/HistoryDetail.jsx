import { useTranslation } from 'react-i18next';
import { useParams, useNavigate } from 'react-router';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Stack from '@mui/material/Stack';
import LinearProgress from '@mui/material/LinearProgress';
import Link from '@mui/material/Link';

import HistoryDetailHeader from '../../../core/components/HistoryDetailHeader';
import ApiDownloadButtons from '../../../core/components/ui/ApiDownloadButtons';
import { exportFileName } from '../../../core/utils/exportData';
import { useHistoryDetail } from '../../../core/hooks/useHistoryDetail';
import FoundSitesList from './FoundSitesList';
import DiscoveredIdentifiers from './DiscoveredIdentifiers';
import { buildPrefillUrl } from '../../../core/utils/crossFeatureNav';
import HudsonRockStatusChip from './HudsonRockStatusChip';
import { useHudsonRockCheck } from '../hooks/api/useHudsonRockCheck';
import { usernameSearchApi } from '../services/api/usernameSearchApi';
import { runSourceLabelKey } from '../utils/sourceLabels';
import { inconclusiveSites } from '../utils/siteCheck';
import ScanStatusChip from '../../../core/components/ScanStatusChip';

const EXPORT_FORMATS = ['csv', 'txt', 'json', 'html', 'pdf', 'xmind'];

export default function HistoryDetail() {
  const { t } = useTranslation('usernameSearch');
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: run, loading } = useHistoryDetail(usernameSearchApi.getRun, id);
  const hudsonRockResult = useHudsonRockCheck(run?.username);

  if (loading) return <LinearProgress />;
  if (!run) return <Typography color="text.secondary">{t('history.notFound')}</Typography>;

  const parentId = run.parent_search_id ?? null;
  const unanswered = run.status === 'completed' ? inconclusiveSites(run.site_statuses) : [];

  return (
    <Box>
      <HistoryDetailHeader
        onBack={() => navigate('/username-search/history')}
        title={run.username}
        chips={(
          <>
            <Chip size="small" variant="outlined" label={t(runSourceLabelKey(run))} />
            <ScanStatusChip status={run.status} label={t(`history.status.${run.status}`)} />
          </>
        )}
        summary={t('history.summary', { checked: run.total_sites_checked, found: run.found_count })}
        error={run.status === 'failed' ? run.error_message : null}
        exportName={exportFileName('username-search', run.username, run.id)}
        exportData={run}
        csvRows={run.site_results}
      />

      {parentId != null && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {/* The parent may have been deleted since; only link to one that still exists. */}
          {run.parent_exists ? (
            <Link component="button" variant="body2" onClick={() => navigate(`/username-search/history/${parentId}`)}>
              {t('history.followedFrom', { id: parentId })}
            </Link>
          ) : t('history.followedFrom', { id: parentId })}
          {run.pivot_source ? ` — ${run.pivot_source}` : ''}
        </Typography>
      )}

      {run.tags && run.tags.length > 0 && (
        <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary">{t('history.tagsUsed')}:</Typography>
          {run.tags.map((tag) => <Chip key={tag} size="small" label={tag} variant="outlined" />)}
        </Stack>
      )}

      {run.has_export && (
        <ApiDownloadButtons
          formats={EXPORT_FORMATS}
          request={(fmt) => usernameSearchApi.exportRequest(run.id, fmt)}
          sx={{ mb: 2 }}
        />
      )}

      <HudsonRockStatusChip result={hudsonRockResult} />
      {unanswered.length > 0 && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {t('scan.siteInconclusive', { sites: unanswered.join(', ') })}
        </Alert>
      )}
      {!(unanswered.length > 0 && run.site_results.length === 0) && <FoundSitesList sites={run.site_results} />}
      {run.status !== 'running' && (
        <DiscoveredIdentifiers
          pivots={run.pivots}
          username={run.username}
          onSearchUsername={(value, { pivotSource } = {}) => navigate(
            buildPrefillUrl('/username-search/new', value, { parent: run.id, src: pivotSource }),
          )}
          onCheckSite={(handle, { pivotSource } = {}) => navigate(
            buildPrefillUrl('/username-search/new', handle.value, { parent: run.id, site: handle.site, src: pivotSource }),
          )}
        />
      )}
    </Box>
  );
}

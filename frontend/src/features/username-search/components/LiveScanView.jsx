import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import LinearProgress from '@mui/material/LinearProgress';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';

import FoundSitesList from './FoundSitesList';
import DiscoveredIdentifiers from './DiscoveredIdentifiers';
import { inconclusiveSites } from '../utils/siteCheck';
import ScanQueuedNotice from '../../../core/components/ui/ScanQueuedNotice';

export default function LiveScanView({ scan, title, onSearchUsername, onCheckSite, searchDisabled }) {
  const { t } = useTranslation('usernameSearch');
  const { phase, queued, source, username, checked, totalSites, currentSite, foundSites, pivots, error, searchId, siteStatuses, cancelScan } = scan;
  const isCoarseProgress = source === 'social_analyzer' || source === 'threat_actor_usernames';
  // A site that was blocked or errored says nothing about the account, so a one-site check that
  // ended that way must not read as "not found".
  const unanswered = source === 'site_check' ? inconclusiveSites(siteStatuses) : [];
  const inconclusive = phase === 'completed' && unanswered.length > 0;
  const progress = totalSites > 0 ? Math.min(100, (checked / totalSites) * 100) : 0;

  return (
    <Box sx={{ mb: 3 }}>
      {title && <Typography variant="subtitle1" sx={{ mb: 1 }}>{title}</Typography>}
      {phase === 'running' && (
        <Box sx={{ mb: 2 }}>
          {queued && <ScanQueuedNotice />}
          <LinearProgress variant={isCoarseProgress ? 'indeterminate' : 'determinate'} value={progress} />
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mt: 0.5 }}>
            <Typography variant="caption">
              {isCoarseProgress
                ? t('scan.scanning')
                : t('scan.progress', { checked, total: totalSites })}
              {!isCoarseProgress && currentSite ? ` — ${t('scan.checking', { site: currentSite })}` : ''}
            </Typography>
            <Button size="small" color="error" startIcon={<CancelIcon />} onClick={cancelScan}>
              {t('scan.cancelButton')}
            </Button>
          </Box>
        </Box>
      )}

      {phase === 'failed' && (
        <Typography color="error" sx={{ mb: 2 }}>
          {t('scan.failed', { error })}
        </Typography>
      )}

      {phase === 'cancelled' && (
        <Chip
          icon={<CancelIcon />}
          color="warning"
          label={t('scan.cancelled', { checked: totalSites, found: foundSites.length })}
          sx={{ mb: 2 }}
        />
      )}

      {inconclusive && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {t('scan.siteInconclusive', { sites: unanswered.join(', ') })}
        </Alert>
      )}

      {phase === 'completed' && !inconclusive && (
        <Chip
          icon={<CheckCircleIcon />}
          color="success"
          label={t('scan.completed', { checked: totalSites, found: foundSites.length })}
          sx={{ mb: 2 }}
        />
      )}

      {!(inconclusive && foundSites.length === 0) && <FoundSitesList sites={foundSites} />}

      {(phase === 'completed' || phase === 'cancelled') && username && onSearchUsername && (
        <DiscoveredIdentifiers
          pivots={pivots}
          username={username}
          onSearchUsername={(value, context) => onSearchUsername(value, { ...context, parentSearchId: searchId })}
          onCheckSite={onCheckSite && ((handle, context) => onCheckSite(handle, { ...context, parentSearchId: searchId }))}
          disabled={searchDisabled}
        />
      )}
    </Box>
  );
}

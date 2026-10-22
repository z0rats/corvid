import { useTranslation } from 'react-i18next';
import { useParams, useNavigate } from 'react-router';
import { useAtomValue } from 'jotai';
import LinearProgress from '@mui/material/LinearProgress';
import Typography from '@mui/material/Typography';

import HistoryDetailHeader from '../../../core/components/HistoryDetailHeader';
import ScanStatusChip from '../../../core/components/ScanStatusChip';
import { exportFileName } from '../../../core/utils/exportData';
import { useHistoryDetail } from '../../../core/hooks/useHistoryDetail';
import ChannelReport from './ChannelReport';
import { telegramSearchApi } from '../services/api/telegramSearchApi';
import { telegramScanStateAtom } from '../state/telegramScanAtoms';

export default function HistoryDetail() {
  const { t } = useTranslation('telegramSearch');
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: search, loading } = useHistoryDetail(telegramSearchApi.getSearch, id);
  // A channel chip starts a new scan, which would take over a running one's live view.
  const scanRunning = useAtomValue(telegramScanStateAtom).phase === 'running';

  if (loading) return <LinearProgress />;
  if (!search) return <Typography color="text.secondary">{t('history.notFound')}</Typography>;

  return (
    <>
      <HistoryDetailHeader
        onBack={() => navigate('/telegram-search/history')}
        title={search.title ? `${search.title} (@${search.channel})` : `@${search.channel}`}
        chips={<ScanStatusChip status={search.status} label={t(`history.status.${search.status}`)} />}
        summary={t('history.summary', {
          count: search.posts_sampled,
          date: new Date(search.started_at).toLocaleString(),
        })}
        error={search.status === 'failed' ? search.error_message : null}
        exportName={exportFileName('telegram', search.channel, search.id)}
        exportData={search}
        csvRows={search.result?.posts}
      />

      <ChannelReport result={search.result} disabled={scanRunning} />
    </>
  );
}

import { useTranslation } from 'react-i18next';
import { useParams, useNavigate } from 'react-router';
import Chip from '@mui/material/Chip';
import LinearProgress from '@mui/material/LinearProgress';
import Typography from '@mui/material/Typography';

import HistoryDetailHeader from '../../../core/components/HistoryDetailHeader';
import { useHistoryDetail } from '../../../core/hooks/useHistoryDetail';
import CheaterReportCard from './CheaterReportCard';
import CloseFriendsTable from './CloseFriendsTable';
import FriendGraphSvg from './FriendGraphSvg';
import GeolocationCard from './GeolocationCard';
import { steamReconApi } from '../services/api/steamReconApi';

const STATUS_COLORS = { running: 'info', completed: 'success', cancelled: 'warning', failed: 'error' };

export default function HistoryDetail() {
  const { t } = useTranslation('steamRecon');
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: search, loading } = useHistoryDetail(steamReconApi.getSearch, id);

  if (loading) return <LinearProgress />;
  if (!search) return <Typography color="text.secondary">{t('history.notFound')}</Typography>;

  const result = search.result;

  return (
    <>
      <HistoryDetailHeader
        onBack={() => navigate('/steam-recon/history')}
        title={search.persona_name || search.target}
        chips={<Chip size="small" label={t(`history.status.${search.status}`)} color={STATUS_COLORS[search.status] || 'default'} />}
        summary={t('history.summary', { analyzed: search.friends_analyzed, total: search.friends_total })}
        error={search.status === 'failed' ? search.error_message : null}
      />

      {result && (
        <>
          <FriendGraphSvg closeFriends={result.close_friends} targetLabel={result.profile.persona_name} />
          <GeolocationCard geolocation={result.geolocation} />
          <CloseFriendsTable closeFriends={result.close_friends} />
          {result.cheater_report && <CheaterReportCard cheaterReport={result.cheater_report} />}
        </>
      )}
    </>
  );
}

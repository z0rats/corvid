import { useTranslation } from 'react-i18next';
import { useParams, useNavigate } from 'react-router';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import LinearProgress from '@mui/material/LinearProgress';

import HistoryDetailHeader from '../../../core/components/HistoryDetailHeader';
import { exportFileName } from '../../../core/utils/exportData';
import { useHistoryDetail } from '../../../core/hooks/useHistoryDetail';
import FoundProvidersList, { FailedChecksNote } from './FoundProvidersList';
import { emailSearchApi } from '../services/api/emailSearchApi';
import ScanStatusChip from '../../../core/components/ScanStatusChip';


export default function HistoryDetail() {
  const { t } = useTranslation('emailSearch');
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: run, loading } = useHistoryDetail(emailSearchApi.getRun, id);

  if (loading) return <LinearProgress />;
  if (!run) return <Typography color="text.secondary">{t('history.notFound')}</Typography>;

  return (
    <Box>
      <HistoryDetailHeader
        onBack={() => navigate('/email-search/history')}
        title={run.username}
        runRef={{ feature: 'email_search', id: run.id }}
        chips={(
          <>
            <Chip size="small" label={t(`form.source.${run.source ?? 'mailcat'}.label`)} />
            <ScanStatusChip status={run.status} label={t(`history.status.${run.status}`)} />
          </>
        )}
        summary={t('history.summary', { checked: run.total_providers_checked, found: run.found_count })}
        error={run.status === 'failed' ? run.error_message : null}
        exportName={exportFileName('email-search', run.username, run.id)}
        exportData={run}
        csvRows={run.provider_results}
      />

      <FailedChecksNote count={run.error_count} />
      <FoundProvidersList
        providers={run.provider_results}
        searchedEmail={run.source === 'user_scanner' ? run.username : undefined}
      />
    </Box>
  );
}

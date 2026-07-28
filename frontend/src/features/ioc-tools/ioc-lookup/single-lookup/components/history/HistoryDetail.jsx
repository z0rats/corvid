import { useTranslation } from 'react-i18next';
import { useParams, useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Stack from '@mui/material/Stack';
import Button from '@mui/material/Button';
import LinearProgress from '@mui/material/LinearProgress';
import DownloadIcon from '@mui/icons-material/Download';

import HistoryDetailHeader from '../../../../../../core/components/HistoryDetailHeader';
import { useHistoryDetail } from '../../../../../../core/hooks/useHistoryDetail';
import HistoryResultTable from './HistoryResultTable';
import { lookupHistoryApi } from '../../services/api/lookupHistoryApi';

const EXPORT_FORMATS = ['html', 'pdf'];

export default function HistoryDetail() {
  const { t, i18n } = useTranslation('iocTools');
  const locale = i18n.language?.startsWith('ru') ? 'ru' : 'en';
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: search, loading } = useHistoryDetail(lookupHistoryApi.getSearch, id);

  if (loading) return <LinearProgress />;
  if (!search) return <Typography color="text.secondary">{t('singleLookup.history.notFound')}</Typography>;

  return (
    <Box>
      <HistoryDetailHeader
        onBack={() => navigate('/ioc-tools/lookup/history')}
        title={search.ioc}
        chips={<Chip size="small" label={search.ioc_type} variant="outlined" />}
        summary={new Date(search.searched_at).toLocaleString()}
      />

      <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: 'wrap' }}>
        {EXPORT_FORMATS.map((fmt) => (
          <Button
            key={fmt}
            size="small"
            variant="outlined"
            startIcon={<DownloadIcon />}
            component="a"
            href={lookupHistoryApi.reportUrl(search.id, fmt, locale)}
            download
          >
            {fmt.toUpperCase()}
          </Button>
        ))}
      </Stack>

      <HistoryResultTable ioc={search.ioc} iocType={search.ioc_type} results={search.results} />
    </Box>
  );
}

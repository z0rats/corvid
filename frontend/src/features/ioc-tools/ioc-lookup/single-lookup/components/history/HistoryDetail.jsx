import { useEffect, useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Stack from '@mui/material/Stack';
import Button from '@mui/material/Button';
import LinearProgress from '@mui/material/LinearProgress';
import IconButton from '@mui/material/IconButton';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import DownloadIcon from '@mui/icons-material/Download';

const EXPORT_FORMATS = ['html', 'pdf'];

import HistoryResultTable from './HistoryResultTable';
import { lookupHistoryApi } from '../../services/api/lookupHistoryApi';
import { createLogger } from '../../../../../../core/utils/logger';

const logger = createLogger('SingleLookupHistoryDetail');

export default function HistoryDetail() {
  const { t, i18n } = useTranslation('iocTools');
  const locale = i18n.language?.startsWith('ru') ? 'ru' : 'en';
  const { id } = useParams();
  const navigate = useNavigate();
  const [search, setSearch] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadSearch = useCallback(async () => {
    try {
      setLoading(true);
      const data = await lookupHistoryApi.getSearch(id);
      setSearch(data);
    } catch (err) {
      logger.error('Failed to load lookup search:', err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { loadSearch(); }, [loadSearch]);

  if (loading) return <LinearProgress />;
  if (!search) return <Typography color="text.secondary">{t('singleLookup.history.notFound')}</Typography>;

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <IconButton onClick={() => navigate('/ioc-tools/lookup/history')}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h5" sx={{ wordBreak: 'break-all' }}>{search.ioc}</Typography>
        <Chip size="small" label={search.ioc_type} variant="outlined" />
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {new Date(search.searched_at).toLocaleString()}
      </Typography>

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

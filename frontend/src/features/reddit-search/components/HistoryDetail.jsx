import { useEffect, useState, useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import LinearProgress from '@mui/material/LinearProgress';
import IconButton from '@mui/material/IconButton';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';

import ResultsList from './ResultsList';
import { redditSearchApi } from '../services/api/redditSearchApi';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('RedditSearchHistoryDetail');

export default function HistoryDetail() {
  const { t } = useTranslation('redditSearch');
  const { id } = useParams();
  const navigate = useNavigate();
  const [search, setSearch] = useState(null);
  const [loading, setLoading] = useState(true);
  const [kind, setKind] = useState('post');

  const loadSearch = useCallback(async () => {
    try {
      setLoading(true);
      const data = await redditSearchApi.getHistory(id);
      setSearch(data);
    } catch (err) {
      logger.error('Failed to load search:', err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { loadSearch(); }, [loadSearch]);

  const { posts, comments } = useMemo(() => {
    const results = search?.results || [];
    return {
      posts: results.filter((r) => r.kind === 'post'),
      comments: results.filter((r) => r.kind === 'comment'),
    };
  }, [search]);

  if (loading) return <LinearProgress />;
  if (!search) return <Typography color="text.secondary">{t('history.notFound')}</Typography>;

  const active = kind === 'post' ? posts : comments;

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <IconButton onClick={() => navigate('/reddit-search/history')}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h5">{search.username}</Typography>
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('history.summary', { count: search.result_count, date: new Date(search.searched_at).toLocaleString() })}
      </Typography>

      <Tabs value={kind} onChange={(_e, value) => setKind(value)} sx={{ mb: 2 }}>
        <Tab value="post" label={t('results.postsTab', { count: posts.length })} />
        <Tab value="comment" label={t('results.commentsTab', { count: comments.length })} />
      </Tabs>

      <ResultsList items={active} sources={['Arctic Shift', 'PullPush']} />
    </Box>
  );
}

import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, useNavigate } from 'react-router';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import LinearProgress from '@mui/material/LinearProgress';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';

import HistoryDetailHeader from '../../../core/components/HistoryDetailHeader';
import { useHistoryDetail } from '../../../core/hooks/useHistoryDetail';
import PostingActivityChart from './PostingActivityChart';
import ResultsList from './ResultsList';
import { redditSearchApi } from '../services/api/redditSearchApi';

export default function HistoryDetail() {
  const { t } = useTranslation('redditSearch');
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: search, loading } = useHistoryDetail(redditSearchApi.getHistory, id);
  const [kind, setKind] = useState('post');

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
      <HistoryDetailHeader
        onBack={() => navigate('/reddit-search/history')}
        title={search.username}
        summary={t('history.summary', { count: search.result_count, date: new Date(search.searched_at).toLocaleString() })}
      />

      <Tabs value={kind} onChange={(_e, value) => setKind(value)} sx={{ mb: 2 }}>
        <Tab value="post" label={t('results.postsTab', { count: posts.length })} />
        <Tab value="comment" label={t('results.commentsTab', { count: comments.length })} />
      </Tabs>

      <PostingActivityChart items={active} />
      <ResultsList items={active} sources={['Arctic Shift', 'PullPush']} />
    </Box>
  );
}

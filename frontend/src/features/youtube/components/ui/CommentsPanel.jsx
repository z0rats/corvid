import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Avatar from '@mui/material/Avatar';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CircularProgress from '@mui/material/CircularProgress';
import Divider from '@mui/material/Divider';
import Link from '@mui/material/Link';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import ThumbUpIcon from '@mui/icons-material/ThumbUpOutlined';

import { useYoutubeComments } from '../../hooks/ui/useYoutubeComments';

function CommentRow({ comment }) {
  return (
    <Stack direction="row" spacing={1.5} sx={{ py: 1 }}>
      <Avatar src={comment.author_profile_image_url} sx={{ width: 32, height: 32 }} />
      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Stack
          direction="row"
          spacing={1}
          sx={{
            alignItems: "baseline",
            flexWrap: 'wrap'
          }}>
          {comment.author_channel_url ? (
            <Link href={comment.author_channel_url} target="_blank" rel="noopener noreferrer" variant="body2" sx={{ fontWeight: 600 }}>
              {comment.author_display_name}
            </Link>
          ) : (
            <Typography variant="body2" sx={{ fontWeight: 600 }}>{comment.author_display_name}</Typography>
          )}
          {comment.published_at && (
            <Typography variant="caption" color="text.secondary">{comment.published_at}</Typography>
          )}
        </Stack>
        <Typography variant="body2" sx={{ whiteSpace: 'pre-line', wordBreak: 'break-word' }}>
          {comment.text}
        </Typography>
        <Stack
          direction="row"
          spacing={0.5}
          sx={{
            alignItems: "center",
            mt: 0.5
          }}>
          <ThumbUpIcon sx={{ fontSize: 14 }} color="action" />
          <Typography variant="caption" color="text.secondary">{comment.like_count}</Typography>
          {comment.reply_count > 0 && (
            <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
              {comment.reply_count}
            </Typography>
          )}
        </Stack>
      </Box>
    </Stack>
  );
}

export default function CommentsPanel({ result }) {
  const { t } = useTranslation('youtube');
  const { video_url: videoUrl, api_configured: apiConfigured } = result;
  const {
    query, setQuery, order, setOrder, loading, error,
    hasSearched, comments, nextPageToken, truncated, search, loadMore,
  } = useYoutubeComments(videoUrl);

  // The page-level ApiKeyRequiredAlert (YoutubeLookup.jsx) already covers the unconfigured
  // case for both this panel and VideoStatsCard - showing it again per-panel here would be a
  // duplicate "add a key" banner for the exact same key.
  if (!apiConfigured) {
    return null;
  }

  const handleKeyDown = (event) => {
    if (event.key === 'Enter') search();
  };

  return (
    <Card sx={{ mb: 2, borderRadius: 1, boxShadow: 0 }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 1 }}>
          {t('comments.title')}
        </Typography>

        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ mb: 1 }}>
          <TextField
            fullWidth
            size="small"
            label={t('comments.searchLabel')}
            placeholder={t('comments.searchPlaceholder')}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <Select size="small" value={order} onChange={(e) => setOrder(e.target.value)} sx={{ minWidth: 150 }}>
            <MenuItem value="relevance">{t('comments.order.relevance')}</MenuItem>
            <MenuItem value="time">{t('comments.order.time')}</MenuItem>
          </Select>
          <Button variant="contained" onClick={search} disabled={loading} sx={{ whiteSpace: 'nowrap' }}>
            {loading && !hasSearched
              ? <CircularProgress size={20} />
              : (query.trim() ? t('comments.searchButton') : t('comments.loadButton'))}
          </Button>
        </Stack>

        {error && <Alert severity="error" sx={{ mb: 1 }}>{error}</Alert>}

        {truncated && (
          <Alert severity="info" variant="outlined" sx={{ mb: 1 }}>
            {t('comments.truncatedNotice')}
          </Alert>
        )}

        {hasSearched && comments.length === 0 && !loading && (
          <Typography variant="body2" color="text.secondary">
            {t('comments.empty')}
          </Typography>
        )}

        {comments.length > 0 && (
          <Stack divider={<Divider />}>
            {comments.map((comment) => <CommentRow key={comment.comment_id} comment={comment} />)}
          </Stack>
        )}

        {nextPageToken && (
          <Box sx={{ textAlign: 'center', mt: 1 }}>
            <Button size="small" onClick={loadMore} disabled={loading}>
              {loading && hasSearched ? <CircularProgress size={16} /> : t('comments.loadMore')}
            </Button>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}

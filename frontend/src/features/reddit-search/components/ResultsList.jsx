import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Link from '@mui/material/Link';

const REDDIT_BASE = 'https://www.reddit.com';

function ResultCard({ item }) {
  const { t } = useTranslation('redditSearch');
  const isPost = item.kind === 'post';
  const createdAt = new Date(item.created_utc * 1000);

  return (
    <Paper
      variant="outlined"
      sx={{
        p: 1.5,
        borderColor: item.removed ? 'error.main' : item.deleted ? 'warning.main' : 'divider',
      }}
    >
      <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" sx={{ mb: 0.5 }}>
        <Typography variant="body2" fontWeight={600}>r/{item.subreddit}</Typography>
        <Typography variant="caption" color="text.secondary">{createdAt.toLocaleString()}</Typography>
        {item.removed && <Chip size="small" color="error" label={t('badges.removed')} />}
        {item.deleted && <Chip size="small" color="warning" label={t('badges.deleted')} />}
        {item.over_18 && <Chip size="small" color="secondary" label={t('badges.nsfw')} />}
        <Typography variant="caption" color="text.secondary" sx={{ ml: 'auto' }}>
          {t('results.score', { score: item.score })}
          {isPost && item.num_comments != null ? ` · ${t('results.comments', { count: item.num_comments })}` : ''}
        </Typography>
      </Stack>

      {isPost && item.title && (
        <Typography variant="subtitle2" sx={{ mb: 0.5 }}>{item.title}</Typography>
      )}

      {item.body && (
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            display: '-webkit-box',
            WebkitLineClamp: 4,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
            whiteSpace: 'pre-wrap',
          }}
        >
          {item.body}
        </Typography>
      )}

      <Link href={`${REDDIT_BASE}${item.permalink}`} target="_blank" rel="noopener noreferrer" variant="caption">
        {t('results.viewOnReddit')}
      </Link>
    </Paper>
  );
}

export default function ResultsList({ items, sources }) {
  const { t } = useTranslation('redditSearch');

  if (!items || items.length === 0) {
    return <Typography color="text.secondary">{t('results.empty')}</Typography>;
  }

  return (
    <Box>
      {sources && sources.length < 2 && (
        <Typography variant="caption" color="warning.main" sx={{ display: 'block', mb: 1 }}>
          {sources.length === 0 ? t('results.bothSourcesDown') : t('results.partialSources', { source: sources[0] })}
        </Typography>
      )}
      <Stack spacing={1}>
        {items.map((item) => (
          <ResultCard key={`${item.kind}-${item.reddit_id}`} item={item} />
        ))}
      </Stack>
    </Box>
  );
}

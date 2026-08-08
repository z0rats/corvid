import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Grid from '@mui/material/Grid';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import CalendarMonthIcon from '@mui/icons-material/CalendarMonthOutlined';
import CategoryIcon from '@mui/icons-material/CategoryOutlined';
import CommentIcon from '@mui/icons-material/CommentOutlined';
import HighQualityIcon from '@mui/icons-material/HighQualityOutlined';
import ThumbUpIcon from '@mui/icons-material/ThumbUpOutlined';
import TimerIcon from '@mui/icons-material/TimerOutlined';
import VisibilityIcon from '@mui/icons-material/VisibilityOutlined';

import { formatCount, formatIsoDuration } from '../../utils/youtubeFormat';

function Field({ icon, label, value, t }) {
  if (!value) return null;
  return (
    <ListItem>
      <ListItemIcon>{icon}</ListItemIcon>
      <ListItemText primary={label} secondary={value || t('stats.notAvailable')} />
    </ListItem>
  );
}

export default function VideoStatsCard({ result }) {
  const { t } = useTranslation('youtube');
  const { api_configured: apiConfigured, api_data: apiData } = result;

  // The page-level ApiKeyRequiredAlert (YoutubeLookup.jsx) already covers the unconfigured
  // case for both this card and CommentsPanel - showing it again per-card here would be a
  // duplicate "add a key" banner for the exact same key.
  if (!apiConfigured) {
    return null;
  }

  if (!apiData) {
    return (
      <Alert severity="warning" variant="outlined" sx={{ borderRadius: 1, mb: 2 }}>
        {t('stats.fetchFailed')}
      </Alert>
    );
  }

  return (
    <Card sx={{ mb: 2, borderRadius: 1, boxShadow: 0 }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 1 }}>
          {t('stats.title')}
        </Typography>
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, sm: 6 }}>
            <List dense>
              <Field t={t} icon={<VisibilityIcon />} label={t('stats.fields.viewCount')} value={formatCount(apiData.view_count)} />
              <Field t={t} icon={<ThumbUpIcon />} label={t('stats.fields.likeCount')} value={formatCount(apiData.like_count)} />
              <Field t={t} icon={<CommentIcon />} label={t('stats.fields.commentCount')} value={formatCount(apiData.comment_count)} />
            </List>
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <List dense>
              <Field t={t} icon={<TimerIcon />} label={t('stats.fields.duration')} value={formatIsoDuration(apiData.duration)} />
              <Field t={t} icon={<CalendarMonthIcon />} label={t('stats.fields.publishedAt')} value={apiData.published_at} />
              <Field t={t} icon={<HighQualityIcon />} label={t('stats.fields.definition')} value={apiData.definition?.toUpperCase()} />
              <Field t={t} icon={<CategoryIcon />} label={t('stats.fields.categoryId')} value={apiData.category_id} />
            </List>
          </Grid>
        </Grid>

        {apiData.tags?.length > 0 && (
          <Stack direction="row" spacing={1} sx={{ mt: 1, gap: 1, flexWrap: 'wrap' }}>
            {apiData.tags.map((tag) => (
              <Chip key={tag} label={tag} size="small" variant="outlined" />
            ))}
          </Stack>
        )}
      </CardContent>
    </Card>
  );
}

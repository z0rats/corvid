import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardMedia from '@mui/material/CardMedia';
import Chip from '@mui/material/Chip';
import Grid from '@mui/material/Grid';
import Link from '@mui/material/Link';
import OpenInNewIcon from '@mui/icons-material/OpenInNewOutlined';
import PersonIcon from '@mui/icons-material/PersonOutlined';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

import { formatIsoDuration } from '../../utils/youtubeFormat';

function MetaRow({ label, value }) {
  if (!value) return null;
  return (
    <Typography variant="body2" color="text.secondary">
      <strong>{label}:</strong> {value}
    </Typography>
  );
}

export default function VideoOverviewCard({ result }) {
  const { t } = useTranslation('youtube');
  const { oembed, page_metadata: pageMetadata, video_url: videoUrl } = result;
  const description = pageMetadata?.description;
  const duration = formatIsoDuration(pageMetadata?.duration);
  const keywords = pageMetadata?.keywords
    ? pageMetadata.keywords.split(',').map((k) => k.trim()).filter(Boolean)
    : [];

  return (
    <Card sx={{ mb: 2, borderRadius: 1, boxShadow: 0 }}>
      <Grid container>
        {oembed.thumbnail_url && (
          <Grid size={{ xs: 12, sm: 4 }}>
            <CardMedia
              component="img"
              image={oembed.thumbnail_url}
              alt={oembed.title || videoUrl}
              sx={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          </Grid>
        )}
        <Grid size={{ xs: 12, sm: oembed.thumbnail_url ? 8 : 12 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 0.5 }}>
              {oembed.title || t('overview.untitled')}
            </Typography>

            <Stack
              direction="row"
              spacing={1}
              sx={{
                alignItems: "center",
                mb: 1,
                flexWrap: 'wrap'
              }}>
              {oembed.author_name && (
                <Chip
                  size="small"
                  icon={<PersonIcon />}
                  label={oembed.author_name}
                  component={oembed.author_url ? Link : 'div'}
                  href={oembed.author_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  clickable={Boolean(oembed.author_url)}
                />
              )}
              <Link href={videoUrl} target="_blank" rel="noopener noreferrer" sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}>
                {t('overview.watchOnYoutube')} <OpenInNewIcon fontSize="inherit" />
              </Link>
            </Stack>

            {description && (
              <Typography variant="body2" sx={{ mb: 1, whiteSpace: 'pre-line' }}>
                {description}
              </Typography>
            )}

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.25 }}>
              <MetaRow label={t('overview.duration')} value={duration} />
              <MetaRow label={t('overview.published')} value={pageMetadata?.date_published || pageMetadata?.upload_date} />
              <MetaRow label={t('overview.genre')} value={pageMetadata?.genre} />
              <MetaRow label={t('overview.channelId')} value={pageMetadata?.channel_id} />
            </Box>

            {keywords.length > 0 && (
              <Stack direction="row" spacing={1} sx={{ mt: 1, gap: 1, flexWrap: 'wrap' }}>
                {keywords.map((keyword) => (
                  <Chip key={keyword} label={keyword} size="small" variant="outlined" />
                ))}
              </Stack>
            )}
          </CardContent>
        </Grid>
      </Grid>
    </Card>
  );
}

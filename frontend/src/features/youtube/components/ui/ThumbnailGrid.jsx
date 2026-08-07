import { useTranslation } from 'react-i18next';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Grid from '@mui/material/Grid';
import Link from '@mui/material/Link';
import Typography from '@mui/material/Typography';

export default function ThumbnailGrid({ thumbnails }) {
  const { t } = useTranslation('youtube');
  const entries = Object.entries(thumbnails || {});
  if (entries.length === 0) return null;

  return (
    <Card sx={{ mb: 2, borderRadius: 1, boxShadow: 0 }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 1 }}>
          {t('thumbnails.title')}
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1.5 }}>
          {t('thumbnails.maxresHint')}
        </Typography>
        <Grid container spacing={2}>
          {entries.map(([variant, url]) => (
            <Grid key={variant} size={{ xs: 6, sm: 4, md: 2.4 }}>
              <Link href={url} target="_blank" rel="noopener noreferrer" underline="none">
                <img
                  src={url}
                  alt={variant}
                  loading="lazy"
                  style={{ width: '100%', borderRadius: 4, display: 'block' }}
                  onError={(e) => { e.currentTarget.style.visibility = 'hidden'; }}
                />
              </Link>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textAlign: 'center', mt: 0.5 }}>
                {variant}
              </Typography>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );
}

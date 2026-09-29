import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Link from '@mui/material/Link';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import BusinessIcon from '@mui/icons-material/BusinessOutlined';
import ImageIcon from '@mui/icons-material/ImageOutlined';
import LockIcon from '@mui/icons-material/LockOutlined';
import OpenInNewIcon from '@mui/icons-material/OpenInNewOutlined';
import VerifiedIcon from '@mui/icons-material/Verified';

function StatBlock({ label, value }) {
  if (value === null || value === undefined) return null;
  return (
    <Box sx={{ textAlign: 'center', minWidth: 72 }}>
      <Typography variant="h6" sx={{ lineHeight: 1.1 }}>{value.toLocaleString()}</Typography>
      <Typography variant="caption" color="text.secondary">{label}</Typography>
    </Box>
  );
}

export default function ProfileOverviewCard({ result }) {
  const { t } = useTranslation('instagramSearch');
  const profileUrl = `https://www.instagram.com/${result.username}/`;
  const hashtags = result.biography_hashtags ?? [];
  const mentions = result.biography_mentions ?? [];

  return (
    <Card sx={{ mb: 2, borderRadius: 1, boxShadow: 0 }}>
      <CardContent>
        <Stack direction="row" spacing={1} sx={{ alignItems: 'center', flexWrap: 'wrap' }}>
          <Typography variant="h6">{result.full_name || `@${result.username}`}</Typography>
          {result.is_verified && (
            <VerifiedIcon color="primary" fontSize="small" titleAccess={t('overview.verified')} />
          )}
          {result.is_private && (
            <Chip size="small" icon={<LockIcon />} label={t('overview.private')} />
          )}
          {result.is_business_account && (
            <Chip
              size="small"
              icon={<BusinessIcon />}
              label={result.business_category_name || t('overview.business')}
            />
          )}
        </Stack>

        <Stack direction="row" spacing={2} sx={{ mt: 0.5, mb: 1.5, flexWrap: 'wrap' }}>
          <Link href={profileUrl} target="_blank" rel="noopener noreferrer" sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}>
            @{result.username} <OpenInNewIcon fontSize="inherit" />
          </Link>
          {result.profile_pic_url && (
            // Link-only, deliberately not an <img> - embedding would leak the analyst's IP to
            // Instagram's CDN and needs a CSP img-src exception (see docs/architecture/instagram-search.md).
            <Link href={result.profile_pic_url} target="_blank" rel="noopener noreferrer" sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}>
              <ImageIcon fontSize="inherit" /> {t('overview.viewProfilePicture')}
            </Link>
          )}
          {result.external_url && (
            <Link href={result.external_url} target="_blank" rel="noopener noreferrer" sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}>
              {result.external_url} <OpenInNewIcon fontSize="inherit" />
            </Link>
          )}
        </Stack>

        {result.biography && (
          <Typography variant="body2" sx={{ mb: 1.5, whiteSpace: 'pre-line' }}>
            {result.biography}
          </Typography>
        )}

        <Stack direction="row" spacing={3}>
          <StatBlock label={t('overview.posts')} value={result.mediacount} />
          <StatBlock label={t('overview.followers')} value={result.followers} />
          <StatBlock label={t('overview.following')} value={result.followees} />
          {result.igtvcount ? <StatBlock label={t('overview.igtv')} value={result.igtvcount} /> : null}
        </Stack>

        {(hashtags.length > 0 || mentions.length > 0) && (
          <Stack direction="row" spacing={1} sx={{ mt: 1.5, gap: 1, flexWrap: 'wrap' }}>
            {hashtags.map((tag) => (
              <Chip key={`hashtag-${tag}`} label={`#${tag}`} size="small" variant="outlined" />
            ))}
            {mentions.map((mention) => (
              <Chip key={`mention-${mention}`} label={`@${mention}`} size="small" variant="outlined" />
            ))}
          </Stack>
        )}
      </CardContent>
    </Card>
  );
}

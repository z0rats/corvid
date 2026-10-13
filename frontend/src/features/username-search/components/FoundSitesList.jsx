import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Link from '@mui/material/Link';
import Chip from '@mui/material/Chip';
import Tooltip from '@mui/material/Tooltip';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import VerifiedIcon from '@mui/icons-material/Verified';

import { sortByConfidence } from '../utils/confidence';

// Strength reads off fill: solid = the notable ratings (confirmed, conflicting), outlined = the
// rest. The theme's primary filled chip is a pale tint, so confirmed uses the solid info blue.
const CONFIDENCE_STYLE = {
  confirmed: { color: 'info', variant: 'filled' },
  likely: { color: 'info', variant: 'outlined' },
  candidate: { color: 'default', variant: 'outlined' },
  conflicting: { color: 'warning', variant: 'filled' },
};

function ConfidenceChip({ level }) {
  const { t } = useTranslation('usernameSearch');
  return (
    <Tooltip title={t(`confidence.hint.${level}`)} describeChild>
      <Chip
        size="small"
        icon={level === 'confirmed' ? <VerifiedIcon /> : undefined}
        {...CONFIDENCE_STYLE[level]}
        label={t(`confidence.${level}`)}
        sx={{ mr: 1 }}
      />
    </Tooltip>
  );
}

export default function FoundSitesList({ sites }) {
  const { t } = useTranslation('usernameSearch');

  if (!sites || sites.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        {t('results.empty')}
      </Typography>
    );
  }

  const rated = sites.some((site) => site.extra?.confidence);

  return (
    <Box>
      <Typography variant="subtitle2" sx={{ mb: 1 }}>
        {t('results.foundCount', { count: sites.length })}
      </Typography>
      {rated && (
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
          {t('confidence.caveat')}
        </Typography>
      )}
      <List dense>
        {sortByConfidence(sites).map((site) => (
          <ListItem key={`${site.site_name}-${site.url_user}`}>
            <ListItemIcon sx={{ minWidth: 32 }}>
              <CheckCircleIcon color="success" fontSize="small" />
            </ListItemIcon>
            <ListItemText
              primary={site.extra?.title || site.site_name}
              secondary={
                site.url_user ? (
                  <Link href={site.url_user} target="_blank" rel="noopener noreferrer">
                    {site.url_user}
                  </Link>
                ) : site.extra?.username ? (
                  t('results.matchedAs', { username: site.extra.username })
                ) : null
              }
            />
            {site.extra?.confidence && <ConfidenceChip level={site.extra.confidence} />}
            {site.extra?.rate && (
              <Typography variant="caption" color="text.secondary">{site.extra.rate}</Typography>
            )}
          </ListItem>
        ))}
      </List>
    </Box>
  );
}

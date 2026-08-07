import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Collapse from '@mui/material/Collapse';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Tooltip from '@mui/material/Tooltip';
import BugReportIcon from '@mui/icons-material/BugReport';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

export default function HudsonRockStatusChip({ result }) {
  const { t } = useTranslation('usernameSearch');
  const [expanded, setExpanded] = useState(false);

  if (!result) return null;

  const count = result.stealers?.length || 0;

  return (
    <Box sx={{ mb: 2 }}>
      <Tooltip title={t('hudsonRock.attribution')}>
        <Chip
          icon={count > 0 ? <BugReportIcon /> : <CheckCircleIcon />}
          color={count > 0 ? 'error' : 'success'}
          label={count > 0 ? t('hudsonRock.found', { count }) : t('hudsonRock.clean')}
          onClick={count > 0 ? () => setExpanded((prev) => !prev) : undefined}
          clickable={count > 0}
        />
      </Tooltip>
      {count > 0 && (
        <Collapse in={expanded}>
          <List dense disablePadding>
            {result.stealers.map((stealer, idx) => (
              <ListItem key={idx} disableGutters>
                <ListItemText
                  primary={`${stealer.computer_name || t('hudsonRock.unknownComputer')} — ${stealer.operating_system || ''}`}
                  secondary={stealer.date_compromised ? new Date(stealer.date_compromised).toLocaleDateString() : null}
                />
              </ListItem>
            ))}
          </List>
        </Collapse>
      )}
    </Box>
  );
}

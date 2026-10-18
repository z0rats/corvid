import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router';
import { formatRelativeTime } from '../../utils/dateFormat';
import Badge from '@mui/material/Badge';
import IconButton from '@mui/material/IconButton';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Popover from '@mui/material/Popover';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import SyncIcon from '@mui/icons-material/Sync';
import { useActiveScans } from '../../hooks/api/useActiveScans';
import { useActivityRows } from '../../hooks/useActivityRows';
import ScanStatusChip from '../ScanStatusChip';

/**
 * AppBar indicator for scans still running or queued behind the heavy-scan limit. Renders
 * nothing while idle, so it only takes space when there's something to wait on; the alerts bell
 * covers what happens once a scan finishes.
 */
export default function ActiveScansMenu() {
  const { t } = useTranslation();
  const [anchorEl, setAnchorEl] = useState(null);
  const { runs, refresh } = useActiveScans();
  const rows = useActivityRows(runs);
  const hasRows = rows.length > 0;

  // The button (the popover's anchor) unmounts once the last scan finishes; forget the open state
  // with it, or the next scan would pop the menu open by itself against a detached node. Adjusted
  // during render (React's pattern for state derived from a prop change), not in an effect.
  if (!hasRows && anchorEl) setAnchorEl(null);

  if (!hasRows) return null;

  const handleOpen = (event) => {
    setAnchorEl(event.currentTarget);
    refresh();
  };
  const handleClose = () => setAnchorEl(null);

  return (
    <>
      <Tooltip title={t('activeScans.title')}>
        <IconButton
          color="inherit"
          onClick={handleOpen}
          aria-label={t('activeScans.ariaLabel', { count: rows.length })}
        >
          <Badge badgeContent={rows.length} color="info" max={99}>
            <SyncIcon
              sx={{
                animation: 'corvid-active-scans-spin 2s linear infinite',
                '@keyframes corvid-active-scans-spin': { to: { transform: 'rotate(360deg)' } },
                '@media (prefers-reduced-motion: reduce)': { animation: 'none' },
              }}
            />
          </Badge>
        </IconButton>
      </Tooltip>
      <Popover
        open={Boolean(anchorEl)}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
        slotProps={{ paper: { sx: { width: 360, maxWidth: 'calc(100vw - 32px)' } } }}
      >
        <Typography variant="subtitle1" sx={{ px: 2, py: 1.5, fontWeight: 600 }}>
          {t('activeScans.title')}
        </Typography>
        <Divider />
        <List dense disablePadding sx={{ maxHeight: 420, overflowY: 'auto' }}>
          {rows.map(({ item, module, path }) => (
            <ListItemButton
              key={`${item.feature}-${item.id}`}
              component={Link}
              to={path}
              onClick={handleClose}
            >
              <ListItemIcon sx={{ minWidth: 36 }}>{module.icon}</ListItemIcon>
              <ListItemText
                primary={item.target}
                secondary={`${module.label} · ${formatRelativeTime(new Date(item.timestamp))}`}
                slotProps={{ primary: { noWrap: true, sx: { fontFamily: '"JetBrains Mono", monospace', fontSize: '0.85rem' } } }}
              />
              <ScanStatusChip status={item.status} label={t(`activeScans.status.${item.status}`)} />
            </ListItemButton>
          ))}
        </List>
      </Popover>
    </>
  );
}

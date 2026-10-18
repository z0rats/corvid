import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';
import { formatRelativeTime } from '../../utils/dateFormat';
import Badge from '@mui/material/Badge';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import IconButton from '@mui/material/IconButton';
import LinearProgress from '@mui/material/LinearProgress';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import Popover from '@mui/material/Popover';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import NotificationsIcon from '@mui/icons-material/NotificationsOutlined';
import { useAlerts } from '../../hooks/api/useAlerts';
import { getAlertLink } from '../../utils/alertLink';
import ConfirmDeleteDialog from './ConfirmDeleteDialog';

// SQLite hands timestamps back without an offset; they're UTC, so don't let Date read them as local.
const parseTimestamp = (value) => new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(value) ? value : `${value}Z`);

/** AppBar bell: unread badge + popover inbox for backend alerts (scan outcomes, jobs, security). */
export default function AlertsMenu() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState(null);
  const [confirmClear, setConfirmClear] = useState(false);
  const { unreadCount, alerts, loading, error, loadAlerts, markRead, markAllRead, clearAll } = useAlerts();

  const handleOpen = (event) => {
    setAnchorEl(event.currentTarget);
    loadAlerts();
  };
  const handleClose = () => setAnchorEl(null);

  const handleAlertClick = (alert) => {
    markRead(alert);
    const link = getAlertLink(alert);
    if (link) {
      handleClose();
      navigate(link);
    }
  };

  return (
    <>
      <Tooltip title={t('alerts.title')}>
        <IconButton
          color="inherit"
          onClick={handleOpen}
          aria-label={t('alerts.ariaLabel', { count: unreadCount })}
        >
          <Badge badgeContent={unreadCount} color="error" max={99}>
            <NotificationsIcon />
          </Badge>
        </IconButton>
      </Tooltip>
      <Popover
        open={Boolean(anchorEl)}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
        slotProps={{ paper: { sx: { width: 380, maxWidth: 'calc(100vw - 32px)' } } }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', px: 2, py: 1.5, gap: 1 }}>
          <Typography variant="subtitle1" sx={{ flexGrow: 1, fontWeight: 600 }}>
            {t('alerts.title')}
          </Typography>
          <Button size="small" onClick={markAllRead} disabled={unreadCount === 0}>
            {t('alerts.markAllRead')}
          </Button>
          <Button size="small" color="error" onClick={() => setConfirmClear(true)} disabled={alerts.length === 0}>
            {t('alerts.clearAll')}
          </Button>
        </Box>
        <Divider />
        {loading && <LinearProgress />}
        {error && (
          <Typography variant="body2" color="error" sx={{ p: 2 }}>{t('alerts.loadFailed')}</Typography>
        )}
        {!loading && !error && alerts.length === 0 && (
          <Typography variant="body2" color="text.secondary" sx={{ p: 2 }}>{t('alerts.empty')}</Typography>
        )}
        {alerts.length > 0 && (
          <List dense disablePadding sx={{ maxHeight: 420, overflowY: 'auto' }}>
            {alerts.map((alert) => (
              <ListItemButton
                key={alert.id}
                onClick={() => handleAlertClick(alert)}
                sx={{
                  display: 'block',
                  borderLeft: 3,
                  borderColor: alert.read ? 'transparent' : 'primary.main',
                  py: 1,
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.25 }}>
                  <Typography
                    variant="body2"
                    sx={{ fontWeight: alert.read ? 400 : 600, flexGrow: 1, minWidth: 0 }}
                    noWrap
                  >
                    {alert.title}
                  </Typography>
                  <Chip label={alert.module} size="small" variant="outlined" sx={{ height: 18, fontSize: '0.65rem' }} />
                </Box>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', wordBreak: 'break-word' }}>
                  {alert.message}
                </Typography>
                <Typography variant="caption" color="text.disabled">
                  {formatRelativeTime(parseTimestamp(alert.timestamp))}
                </Typography>
              </ListItemButton>
            ))}
          </List>
        )}
      </Popover>
      <ConfirmDeleteDialog
        open={confirmClear}
        onClose={() => setConfirmClear(false)}
        onConfirm={() => { setConfirmClear(false); clearAll(); }}
        title={t('alerts.confirmClearTitle')}
        message={t('alerts.confirmClearMessage')}
      />
    </>
  );
}

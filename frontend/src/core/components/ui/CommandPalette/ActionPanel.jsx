import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import OpenInNewIcon from '@mui/icons-material/OpenInNewOutlined';
import PushPinIcon from '@mui/icons-material/PushPinOutlined';
import ContentCopyIcon from '@mui/icons-material/ContentCopyOutlined';
import HealthAndSafetyIcon from '@mui/icons-material/HealthAndSafetyOutlined';
import PlaylistAddIcon from '@mui/icons-material/PlaylistAddOutlined';
import { useTranslation } from 'react-i18next';

/**
 * Per-row action menu (⌘K on a focused row) — generalizes the existing "send to X" chip.
 * IOC-typed tools additionally get Copy / Copy defanged / Add to Bulk Lookup, gated on the
 * row's own `accepts` (see docs/command-palette-plan.md's Action panel section).
 */
export default function ActionPanel({
  anchorEl, entry, value, pinnedIds, onClose, onOpen, onTogglePin, onCopy, onCopyDefanged, onAddToBulk,
}) {
  const { t } = useTranslation('commandPalette');
  if (!entry) return null;

  const hasValue = Boolean(value) && entry.accepts.length > 0;
  const isPinned = pinnedIds.includes(entry.id);

  return (
    <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={onClose}>
      <MenuItem onClick={() => { onOpen(); onClose(); }}>
        <ListItemIcon><OpenInNewIcon fontSize="small" /></ListItemIcon>
        <ListItemText>{t('actionPanel.open')}</ListItemText>
      </MenuItem>
      <MenuItem onClick={() => { onTogglePin(); onClose(); }}>
        <ListItemIcon><PushPinIcon fontSize="small" /></ListItemIcon>
        <ListItemText>{isPinned ? t('actionPanel.unpin') : t('actionPanel.pin')}</ListItemText>
      </MenuItem>
      {hasValue && (
        <MenuItem onClick={() => { onCopy(); onClose(); }}>
          <ListItemIcon><ContentCopyIcon fontSize="small" /></ListItemIcon>
          <ListItemText>{t('actionPanel.copy')}</ListItemText>
        </MenuItem>
      )}
      {hasValue && (
        <MenuItem onClick={() => { onCopyDefanged(); onClose(); }}>
          <ListItemIcon><HealthAndSafetyIcon fontSize="small" /></ListItemIcon>
          <ListItemText>{t('actionPanel.copyDefanged')}</ListItemText>
        </MenuItem>
      )}
      {hasValue && (
        <MenuItem onClick={() => { onAddToBulk(); onClose(); }}>
          <ListItemIcon><PlaylistAddIcon fontSize="small" /></ListItemIcon>
          <ListItemText>{t('actionPanel.addToBulk')}</ListItemText>
        </MenuItem>
      )}
    </Menu>
  );
}

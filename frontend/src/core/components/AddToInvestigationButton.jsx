import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import Divider from '@mui/material/Divider';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import AddIcon from '@mui/icons-material/Add';
import CheckIcon from '@mui/icons-material/Check';
import PlaylistAddIcon from '@mui/icons-material/PlaylistAdd';

import { investigationsService } from '../services/api/investigationsService';
import { useNotification } from '../hooks/ui/useNotification';
import AppSnackbar from './ui/AppSnackbar';
import { createLogger } from '../utils/logger';

const logger = createLogger('AddToInvestigationButton');

/**
 * "Add to investigation" for one stored run: a menu of existing investigations (those already
 * holding the run are checked and disabled) plus "New investigation…". `feature` is the
 * backend's activity-feed name (`ioc_lookup`, `username_search`, ...).
 */
export default function AddToInvestigationButton({ feature, runId }) {
  const { t } = useTranslation();
  const [anchor, setAnchor] = useState(null);
  const [investigations, setInvestigations] = useState([]);
  const [memberIds, setMemberIds] = useState(new Set());
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const { notification, hideNotification, showSuccess, showError } = useNotification();

  const openMenu = async (event) => {
    setAnchor(event.currentTarget);
    try {
      const [all, members] = await Promise.all([
        investigationsService.list(),
        investigationsService.memberships(feature, runId),
      ]);
      setInvestigations(all);
      setMemberIds(new Set(members.map((m) => m.id)));
    } catch (err) {
      logger.error('Failed to load investigations:', err);
      showError(t('investigations.loadFailed'));
    }
  };

  const addTo = async (investigation) => {
    setAnchor(null);
    try {
      await investigationsService.addItem(investigation.id, feature, runId);
      showSuccess(t('investigations.added', { name: investigation.name }));
    } catch (err) {
      logger.error('Failed to add run to investigation:', err);
      showError(t('investigations.addFailed'));
    }
  };

  const createAndAdd = async () => {
    const name = newName.trim();
    if (!name) return;
    setDialogOpen(false);
    setNewName('');
    try {
      await addTo(await investigationsService.create(name));
    } catch (err) {
      logger.error('Failed to create investigation:', err);
      showError(t('investigations.addFailed'));
    }
  };

  return (
    <>
      <Button size="small" variant="outlined" startIcon={<PlaylistAddIcon />} onClick={openMenu}>
        {t('investigations.addButton')}
      </Button>
      <Menu anchorEl={anchor} open={Boolean(anchor)} onClose={() => setAnchor(null)}>
        {investigations.map((investigation) => {
          const member = memberIds.has(investigation.id);
          return (
            <MenuItem key={investigation.id} disabled={member} onClick={() => addTo(investigation)}>
              <ListItemIcon>{member ? <CheckIcon fontSize="small" /> : null}</ListItemIcon>
              <ListItemText
                primary={investigation.name}
                secondary={member ? t('investigations.alreadyAdded') : null}
              />
            </MenuItem>
          );
        })}
        {investigations.length > 0 && <Divider />}
        <MenuItem onClick={() => { setAnchor(null); setDialogOpen(true); }}>
          <ListItemIcon><AddIcon fontSize="small" /></ListItemIcon>
          <ListItemText primary={t('investigations.newInvestigation')} />
        </MenuItem>
      </Menu>
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} fullWidth maxWidth="xs">
        <DialogTitle>{t('investigations.newInvestigation')}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            fullWidth
            margin="dense"
            label={t('investigations.nameLabel')}
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') createAndAdd(); }}
            slotProps={{ htmlInput: { maxLength: 200 } }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>{t('actions.cancel')}</Button>
          <Button variant="contained" onClick={createAndAdd} disabled={!newName.trim()}>
            {t('investigations.createAndAdd')}
          </Button>
        </DialogActions>
      </Dialog>
      <AppSnackbar {...notification} onClose={hideNotification} />
    </>
  );
}

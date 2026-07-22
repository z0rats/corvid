import { useState } from 'react';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import TextField from '@mui/material/TextField';
import PlayArrowIcon from '@mui/icons-material/PlayArrowOutlined';
import EditIcon from '@mui/icons-material/EditOutlined';
import DeleteIcon from '@mui/icons-material/DeleteOutlined';
import CheckIcon from '@mui/icons-material/CheckOutlined';
import { useTranslation } from 'react-i18next';
import Breadcrumbs from './Breadcrumbs';

/** `>playbook:manage` view — list, not an editor (see docs/command-palette-plan.md). */
export default function PlaybookManage({ playbooks, registry, onRename, onDelete, onRunNow, onBack }) {
  const { t } = useTranslation('commandPalette');
  const [editingName, setEditingName] = useState(null);
  const [draftName, setDraftName] = useState('');
  const [runningName, setRunningName] = useState(null);
  const [runValue, setRunValue] = useState('');

  const trailFor = (steps) => steps.map((toolId) => ({
    toolId,
    label: registry.find((e) => e.id === toolId)?.label ?? toolId,
  }));

  const startRename = (name) => {
    setEditingName(name);
    setDraftName(name);
  };

  const commitRename = (oldName) => {
    if (draftName.trim() && draftName.trim() !== oldName) {
      onRename(oldName, draftName.trim());
    }
    setEditingName(null);
  };

  const startRun = (name) => {
    setRunningName(name);
    setRunValue('');
  };

  const commitRun = (name) => {
    onRunNow(name, runValue.trim());
    setRunningName(null);
  };

  if (playbooks.length === 0) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">{t('playbooks.empty')}</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 2, maxHeight: 400, overflowY: 'auto' }}>
      <Typography variant="subtitle2" sx={{ mb: 1 }}>{t('playbooks.title')}</Typography>
      {playbooks.map((playbook) => (
        <Paper key={playbook.name} variant="outlined" sx={{ p: 1.5, mb: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            {editingName === playbook.name ? (
              <TextField
                size="small"
                autoFocus
                value={draftName}
                onChange={(e) => setDraftName(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') commitRename(playbook.name); }}
              />
            ) : (
              <Typography variant="body2" fontWeight="medium">{playbook.name}</Typography>
            )}
            <Box>
              {editingName === playbook.name ? (
                <IconButton size="small" onClick={() => commitRename(playbook.name)} aria-label={t('playbooks.confirmRename')}>
                  <CheckIcon fontSize="small" />
                </IconButton>
              ) : (
                <IconButton size="small" onClick={() => startRename(playbook.name)} aria-label={t('playbooks.rename')}>
                  <EditIcon fontSize="small" />
                </IconButton>
              )}
              <IconButton size="small" onClick={() => startRun(playbook.name)} aria-label={t('playbooks.runNow')}>
                <PlayArrowIcon fontSize="small" />
              </IconButton>
              <IconButton size="small" onClick={() => onDelete(playbook.name)} aria-label={t('playbooks.delete')}>
                <DeleteIcon fontSize="small" />
              </IconButton>
            </Box>
          </Box>
          <Breadcrumbs trail={trailFor(playbook.steps)} />
          {runningName === playbook.name && (
            <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
              <TextField
                size="small"
                fullWidth
                autoFocus
                placeholder={t('playbooks.runValuePlaceholder')}
                value={runValue}
                onChange={(e) => setRunValue(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') commitRun(playbook.name); }}
              />
            </Box>
          )}
        </Paper>
      ))}
      {onBack && (
        <Typography
          variant="body2"
          color="primary"
          sx={{ cursor: 'pointer', mt: 1 }}
          onClick={onBack}
        >
          {t('playbooks.back')}
        </Typography>
      )}
    </Box>
  );
}

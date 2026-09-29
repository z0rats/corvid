import React, { useId, useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useApiKeys } from '../../hooks/api/useApiKeys';
import { useNotification } from '../../../../core/hooks/ui/useNotification';

import NotificationSnackbar from '../ui/NotificationSnackbar';

import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import IconButton from '@mui/material/IconButton';
import InputAdornment from '@mui/material/InputAdornment';
import Switch from '@mui/material/Switch';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import DeleteForeverIcon from '@mui/icons-material/DeleteForever';
import SaveIcon from '@mui/icons-material/Save';

/**
 * A dedicated multiline-paste input for GHunt's session blob (base64 of cookies/OSIDs/an
 * Android master token, several KB) - not a variant of ApiKeyInput, since the interaction
 * genuinely differs (paste a blob, not type a short token; no related-keys/doc-link concept).
 * Saving goes through the validating `PUT /api/email-search/ghunt-profile/session` endpoint
 * (`saveGhuntSession`), not the generic create/update apikey routes - see
 * docs/architecture/ghunt.md.
 */
export default function GhuntSessionInput({ name, description }) {
  const { t } = useTranslation('settings');
  const inputId = useId();

  const [sessionInput, setSessionInput] = useState('');
  const [keyStatus, setKeyStatus] = useState({
    existsInBackend: false,
    isServiceActive: false,
  });

  const { loading, getKeyStatus, saveGhuntSession, deleteApiKey, toggleServiceActivation } = useApiKeys();
  const { notification, showNotification, hideNotification } = useNotification();

  useEffect(() => {
    let ignore = false;

    const fetchKeyStatus = async () => {
      const result = await getKeyStatus(name, []);
      if (ignore) return;
      if (result.success) {
        setKeyStatus(result.data);
        if (!result.data.existsInBackend) {
          setSessionInput('');
        }
      } else {
        showNotification(result.message, 'error');
      }
    };

    fetchKeyStatus();

    return () => { ignore = true; };
  }, [name, getKeyStatus, showNotification]);

  const handleSave = async () => {
    if (!sessionInput.trim()) {
      showNotification(t('notifications.invalidApiKey'), 'warning');
      return;
    }

    const result = await saveGhuntSession(sessionInput);
    if (result.success) {
      setKeyStatus(prev => ({ ...prev, existsInBackend: true, isServiceActive: true }));
      setSessionInput('');
      showNotification(result.message);
    } else {
      showNotification(result.message, 'error');
    }
  };

  const handleDelete = async () => {
    const result = await deleteApiKey(name);
    if (result.success) {
      setKeyStatus(prev => ({ ...prev, existsInBackend: false, isServiceActive: false }));
      setSessionInput('');
      showNotification(result.message);
    } else {
      showNotification(result.message, 'error');
    }
  };

  const handleToggleActivation = async () => {
    const result = await toggleServiceActivation([name], keyStatus.isServiceActive, description);
    if (result.success) {
      setKeyStatus(prev => ({ ...prev, isServiceActive: result.isActive }));
      showNotification(result.message);
    } else {
      showNotification(result.message, 'error');
    }
  };

  return (
    <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
      <TextField
        sx={{ flex: 1, mt: '10px' }}
        id={inputId}
        label={description}
        value={keyStatus.existsInBackend ? '' : sessionInput}
        onChange={(e) => setSessionInput(e.target.value)}
        disabled={keyStatus.existsInBackend || loading}
        multiline
        minRows={keyStatus.existsInBackend ? 1 : 3}
        variant="outlined"
        size="small"
        placeholder={
          keyStatus.existsInBackend
            ? t('ghuntSessionInput.placeholderConfigured')
            : t('ghuntSessionInput.placeholder')
        }
        helperText={!keyStatus.existsInBackend ? t('ghuntSessionInput.helperText') : undefined}
        slotProps={{
          input: {
            endAdornment: (
              <InputAdornment position="end">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  {keyStatus.existsInBackend ? (
                    <Tooltip title={t('ghuntSessionInput.tooltipRemove')}>
                      <IconButton
                        size="small"
                        color="error"
                        onClick={handleDelete}
                        disabled={loading}
                        aria-label={t('ghuntSessionInput.ariaDelete')}
                      >
                        <DeleteForeverIcon />
                      </IconButton>
                    </Tooltip>
                  ) : (
                    <Tooltip title={t('ghuntSessionInput.tooltipSave')}>
                      <IconButton
                        size="small"
                        color="primary"
                        onClick={handleSave}
                        disabled={!sessionInput.trim() || loading}
                        aria-label={t('ghuntSessionInput.ariaSave')}
                      >
                        {loading ? <CircularProgress size={20} /> : <SaveIcon />}
                      </IconButton>
                    </Tooltip>
                  )}
                </Box>
              </InputAdornment>
            ),
          },
        }}
      />

      <Switch
        checked={keyStatus.isServiceActive}
        onChange={handleToggleActivation}
        disabled={loading}
        size="small"
        color="success"
        sx={{ mt: '10px' }}
      />

      <NotificationSnackbar
        notification={notification}
        onClose={hideNotification}
      />
    </Box>
  );
}

import React, { useId, useState, useEffect, useRef } from 'react';
import { useApiKeys } from '../../hooks/api/useApiKeys';
import { useNotification } from '../../../../core/hooks/ui/useNotification';

import { NOTIFICATION_MESSAGES } from '../../constants/settingsConstants';
import NotificationSnackbar from '../ui/NotificationSnackbar';

import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import IconButton from '@mui/material/IconButton';
import InputAdornment from '@mui/material/InputAdornment';
import Link from '@mui/material/Link';
import Switch from '@mui/material/Switch';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import DeleteForeverIcon from '@mui/icons-material/DeleteForever';
import SaveIcon from '@mui/icons-material/Save';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
export default function ApiKeyInput({ name, description, link, relatedKeys = [] }) {
  const inputId = useId();

  const [serviceKeyInput, setServiceKeyInput] = useState('');
  const [keyStatus, setKeyStatus] = useState({
    existsInBackend: false,
    isServiceActive: false,
  });

  const { loading, getKeyStatus, saveApiKey, deleteApiKey, toggleServiceActivation } = useApiKeys();
  const { notification, showNotification, hideNotification } = useNotification();

  const relatedKeysRef = useRef(relatedKeys);
  relatedKeysRef.current = relatedKeys;

  useEffect(() => {
    let ignore = false;

    const fetchKeyStatus = async () => {
      const result = await getKeyStatus(name, relatedKeysRef.current);
      if (ignore) return;
      if (result.success) {
        setKeyStatus(result.data);
        if (!result.data.existsInBackend) {
          setServiceKeyInput('');
        }
      } else {
        showNotification(result.message, 'error');
      }
    };

    fetchKeyStatus();

    return () => { ignore = true; };
  }, [name, getKeyStatus, showNotification]);

  const handleSaveApiKey = async () => {
    if (!serviceKeyInput.trim()) {
      showNotification(NOTIFICATION_MESSAGES.INVALID_API_KEY, 'warning');
      return;
    }

    const result = await saveApiKey(name, serviceKeyInput);
    if (result.success) {
      setKeyStatus(prev => ({ ...prev, existsInBackend: true, isServiceActive: true }));
      showNotification(result.message);
    } else {
      showNotification(result.message, 'error');
    }
  };

  const handleDeleteApiKey = async () => {
    const result = await deleteApiKey(name);
    if (result.success) {
      setKeyStatus(prev => ({ ...prev, existsInBackend: false, isServiceActive: false }));
      setServiceKeyInput('');
      showNotification(result.message);
    } else {
      showNotification(result.message, 'error');
    }
  };

  // Handle service activation toggle
  const handleToggleActivation = async () => {
    const keysToToggle = [name, ...relatedKeys];
    const result = await toggleServiceActivation(keysToToggle, keyStatus.isServiceActive, description);
    
    if (result.success) {
      setKeyStatus(prev => ({ ...prev, isServiceActive: result.isActive }));
      showNotification(result.message);
    } else {
      showNotification(result.message, 'error');
    }
  };

  return (
    <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
      {/* API Key Input Field */}
      <TextField
        sx={{ flex: 1, mt: '10px' }}
        id={inputId}
        label={description}
        value={keyStatus.existsInBackend ? '••••••••••••••••' : serviceKeyInput}
        type="password"
        onChange={(e) => setServiceKeyInput(e.target.value)}
        disabled={keyStatus.existsInBackend || loading}
        variant="outlined"
        size="small"
        placeholder={keyStatus.existsInBackend ? 'API key configured' : 'Enter your API key...'}
        slotProps={{
          input: {
            endAdornment: (
              <InputAdornment position="end">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  {keyStatus.existsInBackend ? (
                    <Tooltip title="Remove API Key">
                      <IconButton
                        size="small"
                        color="error"
                        onClick={handleDeleteApiKey}
                        disabled={loading}
                        aria-label="Delete API key"
                      >
                        <DeleteForeverIcon />
                      </IconButton>
                    </Tooltip>
                  ) : (
                    <>
                      <Tooltip title="Get API Key">
                        <IconButton
                          size="small"
                          component={Link}
                          href={link}
                          target="_blank"
                          rel="noopener noreferrer"
                          aria-label="Get API key"
                        >
                          <OpenInNewIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Save API Key">
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={handleSaveApiKey}
                          disabled={!serviceKeyInput.trim() || loading}
                          aria-label="Save API key"
                        >
                          {loading ? <CircularProgress size={20} /> : <SaveIcon />}
                        </IconButton>
                      </Tooltip>
                    </>
                  )}
                </Box>
              </InputAdornment>
            ),
          },
        }}
      />

      {/* Activation Toggle Switch */}
      <Switch
        checked={keyStatus.isServiceActive}
        onChange={handleToggleActivation}
        disabled={loading}
        size="small"
        color="success"
      />

      {/* Help Text for unconfigured keys */}
      {!keyStatus.existsInBackend && (
        <Box sx={{ position: 'absolute', mt: '70px', display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="caption" color="text.secondary">
            No API key?
          </Typography>
          <Link
            href={link}
            target="_blank"
            rel="noopener noreferrer"
            variant="caption"
            sx={{ display: 'flex', alignItems: 'center', gap: 0.5, textDecoration: 'none' }}
          >
            Create it here
            <OpenInNewIcon sx={{ fontSize: 12 }} />
          </Link>
        </Box>
      )}

      <NotificationSnackbar 
        notification={notification} 
        onClose={hideNotification} 
      />
    </Box>
  );
}

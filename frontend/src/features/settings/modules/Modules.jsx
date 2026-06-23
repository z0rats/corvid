import React from 'react';
import { useAtomValue } from 'jotai';
import { modulesState } from '../../../core/state/atoms';
import { useModules } from '../hooks/api/useModules';
import { useNotification } from '../../../core/hooks/ui/useNotification';
import { formatModuleName } from '../utils/settingsUtils';
import { VALID_MODULE_IDS, MODULE_DESCRIPTIONS } from '../constants/settingsConstants';
import NotificationSnackbar from '../components/ui/NotificationSnackbar';

import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CircularProgress from '@mui/material/CircularProgress';
import Switch from '@mui/material/Switch';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';

export default function Modules() {
  const modules = useAtomValue(modulesState);
  const { loading, toggleModule } = useModules();
  const { notification, showNotification, hideNotification } = useNotification();

  const handleModuleToggle = async (moduleName) => {
    const currentEnabled = modules[moduleName]?.enabled || false;
    const result = await toggleModule(moduleName, currentEnabled);

    if (result.success) {
      showNotification(result.message);
    } else {
      showNotification(result.message, 'error');
    }
  };

  const filteredModules = Object.entries(modules).filter(([name]) =>
    VALID_MODULE_IDS.includes(name)
  );

  if (!modules || filteredModules.length === 0) {
    return (
      <Box sx={{ maxWidth: '800px', mx: 'auto' }}>
        <Alert severity="info">Loading modules...</Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Card elevation={0} sx={{ border: 'none' }}>
        <CardContent>
          <Typography variant="h5" sx={{ mb: 2 }}>
            Modules
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Enable or disable modules based on your needs.
          </Typography>

          <Grid container spacing={2}>
            {filteredModules.map(([name, module]) => (
              <Grid size={{ xs: 12, md: 6 }} key={name}>
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    p: 2,
                    borderRadius: 1,
                    border: '1px solid',
                    borderColor: 'divider',
                    height: '100%',
                    bgcolor: 'action.hover',
                  }}
                >
                  <Box>
                    <Typography variant="h6">{formatModuleName(name)}</Typography>
                    {MODULE_DESCRIPTIONS[name] && (
                      <Typography variant="body2" color="text.secondary">
                        {MODULE_DESCRIPTIONS[name]}
                      </Typography>
                    )}
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {loading && (
                      <CircularProgress size={20} />
                    )}
                    <Switch
                      checked={!!module.enabled}
                      onChange={() => handleModuleToggle(name)}
                      disabled={loading}
                      color="primary"
                    />
                  </Box>
                </Box>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>

      <NotificationSnackbar
        notification={notification}
        onClose={hideNotification}
      />
    </Box>
  );
}

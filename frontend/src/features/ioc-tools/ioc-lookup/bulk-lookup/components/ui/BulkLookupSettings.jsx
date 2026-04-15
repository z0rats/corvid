import React, { useState, useCallback } from 'react';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Switch from '@mui/material/Switch';
import Typography from '@mui/material/Typography';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import SettingsIcon from '@mui/icons-material/Settings';
import { iocLookupApi } from '../../../../shared/services/api/iocLookupApi';
import { createLogger } from '../../../../../../core/utils/logger';

const logger = createLogger('BulkLookupSettings');

export default function BulkLookupSettings({ services, onSettingsChange, serviceDefinitions }) {
  const [error, setError] = useState('');

  const handleToggle = useCallback((serviceName, currentValue) => {
    setError('');
    const newValue = !currentValue;
    const serviceDef = serviceDefinitions[serviceName];

    const keysToUpdate = (serviceDef?.requiredKeys && serviceDef.requiredKeys.length > 0)
      ? serviceDef.requiredKeys
      : [serviceName];

    const updatePromises = keysToUpdate.map(keyName =>
      iocLookupApi.updateBulkLookupSetting(keyName, newValue)
    );

    Promise.all(updatePromises)
      .then(() => {
        if (onSettingsChange) {
          onSettingsChange();
        }
      })
      .catch(err => {
        logger.error(`Failed to update setting for ${serviceName}:`, err);
        setError(`Failed to update setting for ${serviceName}.`);
      });
  }, [serviceDefinitions, onSettingsChange]);

  return (
    <Accordion sx={{ mb: 2, boxShadow: 1, '&:before': { display: 'none' } }}>
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        aria-controls="bulk-settings-content"
        id="bulk-settings-header"
      >
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <SettingsIcon sx={{ mr: 1, color: 'text.secondary' }} />
          <Typography>Bulk IOC Lookup Settings</Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails>
        {error && <Alert severity="error" onClose={() => setError('')}>{error}</Alert>}
        {services.length > 0 ? (
          <List dense>
            {[...services]
              .sort((a, b) => a.name.localeCompare(b.name))
              .map(({ name, is_bulk_lookup_enabled }) => (
                <ListItem key={name} secondaryAction={
                  <Switch
                    edge="end"
                    onChange={() => handleToggle(name, is_bulk_lookup_enabled)}
                    checked={is_bulk_lookup_enabled}
                    slotProps={{
                      input: { 'aria-labelledby': `switch-list-label-${name}` },
                    }}
                  />
                }>
                  <ListItemText
                    id={`switch-list-label-${name}`}
                    primary={serviceDefinitions[name]?.name || name}
                  />
                </ListItem>
              ))}
          </List>
        ) : (
          <Typography variant="body2" color="text.secondary" sx={{ p: 2, textAlign: 'center' }}>
            No services with API keys are configured. Please add keys in the main settings tab to enable them here.
          </Typography>
        )}
      </AccordionDetails>
    </Accordion>
  );
}
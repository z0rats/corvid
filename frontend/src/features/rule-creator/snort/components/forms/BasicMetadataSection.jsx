import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import AddCircleIcon from '@mui/icons-material/AddCircle';
import DeleteIcon from '@mui/icons-material/Delete';
import InfoIcon from '@mui/icons-material/Info';

export default function BasicMetadataSection({ metadata, onMetadataChange }) {
  const { t } = useTranslation('ruleCreator');
  const [currentMetadata, setCurrentMetadata] = useState({ key: '', value: '' });

  const handleAdd = () => {
    if (!currentMetadata.key.trim() || !currentMetadata.value.trim()) {
      alert(t('snort.basicMetadataSection.requiredAlert'));
      return;
    }
    onMetadataChange([...metadata, {
      id: crypto.randomUUID(),
      key: currentMetadata.key.trim(),
      value: currentMetadata.value.trim(),
    }]);
    setCurrentMetadata({ key: '', value: '' });
  };

  const handleDelete = (idToDelete) => {
    onMetadataChange(metadata.filter((meta) => meta.id !== idToDelete));
  };

  return (
    <Box sx={{ mt: 3 }}>
      <Typography variant="subtitle2" gutterBottom>
        {t('snort.basicMetadataSection.header')}
      </Typography>
      <Grid container spacing={1} alignItems="center">
        <Grid size={{ xs: 12, sm: 4 }}>
          <TextField
            fullWidth
            label={t('snort.basicMetadataSection.keyLabel')}
            value={currentMetadata.key}
            onChange={(e) => setCurrentMetadata(prev => ({ ...prev, key: e.target.value }))}
            size="small"
            variant="outlined"
            placeholder={t('snort.basicMetadataSection.keyPlaceholder')}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <TextField
            fullWidth
            label={t('snort.basicMetadataSection.valueLabel')}
            value={currentMetadata.value}
            onChange={(e) => setCurrentMetadata(prev => ({ ...prev, value: e.target.value }))}
            size="small"
            variant="outlined"
            placeholder={t('snort.basicMetadataSection.valuePlaceholder')}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 2 }}>
          <Button
            variant="contained"
            startIcon={<AddCircleIcon />}
            onClick={handleAdd}
            disabled={!currentMetadata.key.trim() || !currentMetadata.value.trim()}
            size="small"
            fullWidth
          >
            {t('common.actions.add')}
          </Button>
        </Grid>
      </Grid>

      {metadata.length > 0 && (
        <List sx={{ mt: 1, maxHeight: 150, overflow: 'auto' }}>
          {metadata.map((meta) => (
            <ListItem
              key={meta.id}
              secondaryAction={
                <Tooltip title={t('snort.basicMetadataSection.deleteTooltip')}>
                  <IconButton edge="end" onClick={() => handleDelete(meta.id)} size="small" aria-label={t('snort.basicMetadataSection.deleteAria')}>
                    <DeleteIcon fontSize="small" color="error" />
                  </IconButton>
                </Tooltip>
              }
              sx={{ py: 0.5 }}
            >
              <ListItemIcon sx={{ minWidth: 30 }}>
                <InfoIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText primary={`${meta.key}: ${meta.value}`} />
            </ListItem>
          ))}
        </List>
      )}
    </Box>
  );
}

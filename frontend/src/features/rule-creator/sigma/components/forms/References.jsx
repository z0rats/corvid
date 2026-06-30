import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import DeleteIcon from '@mui/icons-material/Delete';
import AddCircleIcon from '@mui/icons-material/AddCircle';
import LinkIcon from '@mui/icons-material/Link';

export default function References({ references, handleReferencesChange }) {
  const { t } = useTranslation('ruleCreator');
  const [currentReference, setCurrentReference] = useState('');

  const handleAddReference = () => {
    const trimmedReference = currentReference.trim();
    if (trimmedReference && !references.some((ref) => ref.value === trimmedReference)) {
      handleReferencesChange((prev) => [...prev, { id: crypto.randomUUID(), value: trimmedReference }]);
      setCurrentReference('');
    }
  };

  const handleDeleteReference = (idToDelete) => {
    handleReferencesChange((prev) => prev.filter((ref) => ref.id !== idToDelete));
  };

  return (
    <Box> 
      <Typography variant="subtitle2" gutterBottom>
        {t('sigma.references.helpText')}
      </Typography>
      <Typography variant="body2" ml={2} gutterBottom component="div">
        <ul>
          <li>{t('sigma.references.guidanceLinksOnly')}</li>
          <li>{t('sigma.references.guidanceNoRawContent')}</li>
          <li>{t('sigma.references.guidanceNoMitreLinks')}</li>
        </ul>
      </Typography>
      <Typography variant="caption" gutterBottom>
        {t('sigma.references.examplesCaption')}
      </Typography>
      <TextField
        fullWidth
        label={t('sigma.references.label')}
        value={currentReference}
        onChange={(e) => setCurrentReference(e.target.value)}
        size="small"
        variant="outlined"
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            handleAddReference();
          }
        }}
        placeholder={t('sigma.references.placeholder')}
        slotProps={{
          input: {
            endAdornment: (
              <Tooltip title={t('sigma.references.addTooltip')}>
                <IconButton
                  onClick={handleAddReference}
                  disabled={!currentReference.trim()}
                  size="small"
                  aria-label={t('sigma.references.addAria')}
                >
                  <AddCircleIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            ),
          },
        }}
        sx={{ mt: 2 }} 
      />
      {/* List of References */}
      {references.length > 0 && (
        <List sx={{ mt: 2, maxHeight: 150, overflow: 'auto' }}>
          {references.map((ref) => (
            <ListItem
              key={ref.id}
              secondaryAction={
                <IconButton
                  edge="end"
                  onClick={() => handleDeleteReference(ref.id)}
                  size="small"
                  aria-label={t('sigma.references.deleteAria')}
                >
                  <DeleteIcon fontSize="small" color="error" />
                </IconButton>
              }
              sx={{ py: 0.5 }}
            >
              <ListItemIcon sx={{ minWidth: 30 }}>
                <LinkIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText primary={ref.value} />
            </ListItem>
          ))}
        </List>
      )}
    </Box>
  );
}

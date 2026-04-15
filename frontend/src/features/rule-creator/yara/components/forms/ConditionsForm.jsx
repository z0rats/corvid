import React from 'react';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid2';
import SecurityIcon from '@mui/icons-material/Security';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { FILE_TYPES, CONDITION_TYPES } from '../../constants/yaraConstants';

/**
 * Form component for YARA rule conditions
 * @param {Object} props - Component props
 * @param {Object} props.conditions - Current conditions state
 * @param {Function} props.onConditionsChange - Handler for conditions changes
 * @param {Function} props.onStringMatchChange - Handler for string match condition changes
 */
export default function ConditionsForm({ 
  conditions, 
  onConditionsChange, 
  onStringMatchChange 
}) {
  const handleStringMatchChange = (event) => {
    const value = event.target.value;
    onStringMatchChange(value);
  };

  const handleFieldChange = (field) => (event) => {
    onConditionsChange(field, event.target.value);
  };

  const getStringMatchValue = () => {
    if (conditions.all) return CONDITION_TYPES.ALL;
    if (conditions.any) return CONDITION_TYPES.ANY;
    return CONDITION_TYPES.NONE;
  };

  return (
    <Accordion sx={{ border: 'none', boxShadow: 'none', mt: 1 }}>
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        sx={{
          px: 1,
          py: 0.5,
          minHeight: '40px',
          '& .MuiAccordionSummary-content': {
            margin: 0,
          },
        }}
      >
        <Box display="flex" alignItems="center">
          <SecurityIcon fontSize="small" sx={{ mr: 1 }} />
          <Typography variant="subtitle2">Conditions</Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ px: 1, py: 1 }}>
        <Grid container spacing={1}>
          <Grid size={{ xs: 12, sm: 4 }}>
            <FormControl fullWidth size="small">
              <InputLabel>String Match</InputLabel>
              <Select
                value={getStringMatchValue()}
                label="String Match"
                onChange={handleStringMatchChange}
              >
                <MenuItem value={CONDITION_TYPES.NONE}>None</MenuItem>
                <MenuItem value={CONDITION_TYPES.ALL}>All of them</MenuItem>
                <MenuItem value={CONDITION_TYPES.ANY}>Any of them</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid size={{ xs: 6, sm: 4 }}>
            <TextField
              fullWidth
              label="File Size (KB)"
              type="number"
              value={conditions.filesize}
              onChange={handleFieldChange('filesize')}
              size="small"
              variant="outlined"
              slotProps={{ htmlInput: { min: 0 } }}
              placeholder="e.g., 1024"
            />
          </Grid>
          <Grid size={{ xs: 6, sm: 4 }}>
            <FormControl fullWidth size="small">
              <InputLabel>File Type</InputLabel>
              <Select
                value={conditions.filetype}
                label="File Type"
                onChange={handleFieldChange('filetype')}
              >
                <MenuItem value="">None</MenuItem>
                {FILE_TYPES.map((type) => (
                  <MenuItem key={type} value={type}>
                    {type.toUpperCase()}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>
        
        {/* Help text */}
        <Box sx={{ mt: 1 }}>
          <Typography variant="caption" color="text.secondary">
            Conditions define when the rule should match. String match conditions require at least one string to be defined.
          </Typography>
        </Box>
      </AccordionDetails>
    </Accordion>
  );
}

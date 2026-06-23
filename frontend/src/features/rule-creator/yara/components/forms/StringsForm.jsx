import React from 'react';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Autocomplete from '@mui/material/Autocomplete';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import AddCircleIcon from '@mui/icons-material/AddCircle';
import CodeIcon from '@mui/icons-material/Code';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { STRING_TYPES, STRING_MODIFIERS } from '../../constants/yaraConstants';

/**
 * Form component for adding YARA rule strings
 * @param {Object} props - Component props
 * @param {Object} props.currentString - Current string being edited
 * @param {Function} props.onCurrentStringChange - Handler for current string changes
 * @param {Function} props.onAddString - Handler for adding a string
 * @param {boolean} props.canAddString - Whether a string can be added
 * @param {Object} props.errors - Validation errors
 * @param {Function} props.onClearError - Handler to clear specific errors
 */
export default function StringsForm({ 
  currentString, 
  onCurrentStringChange, 
  onAddString,
  canAddString,
  errors = {},
  onClearError 
}) {
  const handleFieldChange = (field) => (event) => {
    onCurrentStringChange(field, event.target.value);
    if (errors[field] && onClearError) {
      onClearError(field);
    }
  };

  const handleModifiersChange = (event, newValue) => {
    onCurrentStringChange('modifiers', newValue);
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && canAddString) {
      event.preventDefault();
      onAddString();
    }
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
          <CodeIcon fontSize="small" sx={{ mr: 1 }} />
          <Typography variant="subtitle2">Add String</Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ px: 1, py: 1 }}>
        <Grid container spacing={1} alignItems="center">
          <Grid size={{ xs: 12, sm: 3 }}>
            <TextField
              fullWidth
              label="Identifier"
              value={currentString.identifier}
              onChange={handleFieldChange('identifier')}
              onKeyPress={handleKeyPress}
              required
              size="small"
              variant="outlined"
              error={!!errors.identifier}
              helperText={errors.identifier}
              placeholder="e.g., malware_string"
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 2 }}>
            <FormControl fullWidth size="small">
              <InputLabel>Type</InputLabel>
              <Select
                value={currentString.type}
                label="Type"
                onChange={handleFieldChange('type')}
              >
                {STRING_TYPES.map((type) => (
                  <MenuItem key={type} value={type}>
                    {type.toUpperCase()}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid size={{ xs: 12, sm: 4 }}>
            <TextField
              fullWidth
              label="Value"
              value={currentString.value}
              onChange={handleFieldChange('value')}
              onKeyPress={handleKeyPress}
              required
              size="small"
              variant="outlined"
              error={!!errors.value}
              helperText={errors.value}
              placeholder={getPlaceholderForType(currentString.type)}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 2 }}>
            <Autocomplete
              multiple
              options={STRING_MODIFIERS}
              value={currentString.modifiers}
              onChange={handleModifiersChange}
              renderInput={(params) => (
                <TextField 
                  {...params} 
                  label="Modifiers" 
                  placeholder="Select" 
                  size="small" 
                />
              )}
              size="small"
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 1 }}>
            <Button
              variant="contained"
              startIcon={<AddCircleIcon />}
              onClick={onAddString}
              disabled={!canAddString}
              size="small"
              fullWidth
            >
              Add
            </Button>
          </Grid>
        </Grid>
      </AccordionDetails>
    </Accordion>
  );
}

/**
 * Get placeholder text based on string type
 * @param {string} type - String type
 * @returns {string} Placeholder text
 */
function getPlaceholderForType(type) {
  switch (type) {
    case 'hex':
      return 'e.g., 4D 5A 90 00';
    case 'regex':
      return 'e.g., /malware[0-9]+/';
    case 'wide':
      return 'e.g., wide string';
    default:
      return 'e.g., malicious string';
  }
}

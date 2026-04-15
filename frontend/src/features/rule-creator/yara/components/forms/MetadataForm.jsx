import React from 'react';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid2';
import DescriptionIcon from '@mui/icons-material/Description';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

/**
 * Form component for YARA rule metadata
 * @param {Object} props - Component props
 * @param {Object} props.metadata - Current metadata state
 * @param {Function} props.onMetadataChange - Handler for metadata changes
 * @param {Object} props.errors - Validation errors
 * @param {Function} props.onClearError - Handler to clear specific errors
 */
export default function MetadataForm({ 
  metadata, 
  onMetadataChange, 
  errors = {}, 
  onClearError 
}) {
  const handleFieldChange = (field) => (event) => {
    onMetadataChange(field, event.target.value);
    if (errors[field] && onClearError) {
      onClearError(field);
    }
  };

  return (
    <Accordion sx={{ border: 'none', boxShadow: 'none' }} defaultExpanded>
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
          <DescriptionIcon fontSize="small" sx={{ mr: 1 }} />
          <Typography variant="subtitle2">Rule Metadata</Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ px: 1, py: 1 }}>
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth
              label="Rule Name"
              value={metadata.ruleName}
              onChange={handleFieldChange('ruleName')}
              required
              size="small"
              variant="outlined"
              error={!!errors.ruleName}
              helperText={errors.ruleName}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth
              label="Author"
              value={metadata.author}
              onChange={handleFieldChange('author')}
              size="small"
              variant="outlined"
            />
          </Grid>
          <Grid size={12}>
            <TextField
              fullWidth
              label="Description"
              multiline
              rows={2}
              value={metadata.description}
              onChange={handleFieldChange('description')}
              size="small"
              variant="outlined"
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth
              label="Reference"
              value={metadata.reference}
              onChange={handleFieldChange('reference')}
              size="small"
              variant="outlined"
            />
          </Grid>
          <Grid size={{ xs: 6, sm: 3 }}>
            <TextField
              fullWidth
              label="Hash"
              value={metadata.hash}
              onChange={handleFieldChange('hash')}
              size="small"
              variant="outlined"
            />
          </Grid>
          <Grid size={{ xs: 6, sm: 3 }}>
            <TextField
              fullWidth
              label="Version"
              value={metadata.version}
              onChange={handleFieldChange('version')}
              size="small"
              variant="outlined"
            />
          </Grid>
        </Grid>
      </AccordionDetails>
    </Accordion>
  );
}

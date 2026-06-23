import React from 'react';
import Autocomplete from '@mui/material/Autocomplete';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import TextField from '@mui/material/TextField';
import Grid from '@mui/material/Grid';
import { SNORT_CONSTANTS } from '../../constants/snortConstants';
import CustomTagsSection from './CustomTagsSection';
import MalwareFamilySection from './MalwareFamilySection';

export default function RuleMetadata({ ruleMetadata, handleRuleMetadataChange }) {
  const handleChange = (field, value) => {
    handleRuleMetadataChange(prev => ({ ...prev, [field]: value }));
  };

  const handleTagsChange = (newTags) => {
    handleRuleMetadataChange(prev => ({ ...prev, tag: newTags }));
  };

  const handleFamiliesChange = (newFamilies) => {
    handleRuleMetadataChange(prev => ({ ...prev, malware_family: newFamilies }));
  };

  return (
    <Box>
      <Grid container spacing={2}>
        <Grid size={{ xs: 6, sm: 4 }}>
          <TextField
            fullWidth
            label="Created At"
            type="date"
            value={ruleMetadata.created_at}
            onChange={(e) => handleChange('created_at', e.target.value)}
            size="small"
            variant="outlined"
            slotProps={{ inputLabel: { shrink: true } }}
          />
        </Grid>

        <Grid size={{ xs: 6, sm: 4 }}>
          <TextField
            fullWidth
            label="Updated At"
            type="date"
            value={ruleMetadata.updated_at}
            onChange={(e) => handleChange('updated_at', e.target.value)}
            size="small"
            variant="outlined"
            slotProps={{ inputLabel: { shrink: true } }}
          />
        </Grid>

        <Grid size={{ xs: 12, sm: 4 }}>
          <FormControl fullWidth size="small">
            <InputLabel>Policy</InputLabel>
            <Select
              value={ruleMetadata.policy}
              label="Policy"
              onChange={(e) => handleChange('policy', e.target.value)}
            >
              <MenuItem value="">None</MenuItem>
              {['Balanced', 'Connectivity', 'Security', 'Max-Detect'].map((policy) => (
                <MenuItem key={policy} value={policy}>
                  {policy}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        <Grid size={{ xs: 12, sm: 6 }}>
          <FormControl fullWidth size="small">
            <InputLabel>Former Category</InputLabel>
            <Select
              value={ruleMetadata.former_category}
              label="Former Category"
              onChange={(e) => handleChange('former_category', e.target.value)}
            >
              <MenuItem value="">None</MenuItem>
              {SNORT_CONSTANTS.CLASSTYPES.map((category) => (
                <MenuItem key={category} value={category}>
                  {category}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        <Grid size={{ xs: 12, sm: 6 }}>
          <FormControl fullWidth size="small">
            <InputLabel>Signature Severity</InputLabel>
            <Select
              value={ruleMetadata.signature_severity}
              label="Signature Severity"
              onChange={(e) => handleChange('signature_severity', e.target.value)}
            >
              <MenuItem value="">None</MenuItem>
              {SNORT_CONSTANTS.SIGNATURE_SEVERITIES.map((severity) => (
                <MenuItem key={severity} value={severity}>
                  {severity}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        <Grid size={{ xs: 12, sm: 6 }}>
          <Autocomplete
            multiple
            options={SNORT_CONSTANTS.ATTACK_TARGETS}
            value={ruleMetadata.attack_target}
            onChange={(_, newValue) => handleChange('attack_target', newValue)}
            renderInput={(params) => (
              <TextField {...params} label="Attack Target" placeholder="Select targets" size="small" />
            )}
            renderTags={(value, getTagProps) =>
              value.map((option, index) => (
                <Chip variant="outlined" label={option} size="small" {...getTagProps({ index })} />
              ))
            }
            size="small"
          />
        </Grid>

        <Grid size={{ xs: 12, sm: 6 }}>
          <Autocomplete
            multiple
            options={SNORT_CONSTANTS.DEPLOYMENTS}
            value={ruleMetadata.deployment}
            onChange={(_, newValue) => handleChange('deployment', newValue)}
            renderInput={(params) => (
              <TextField {...params} label="Deployment" placeholder="Select deployments" size="small" />
            )}
            renderTags={(value, getTagProps) =>
              value.map((option, index) => (
                <Chip variant="outlined" label={option} size="small" {...getTagProps({ index })} />
              ))
            }
            size="small"
          />
        </Grid>
      </Grid>

      <CustomTagsSection tags={ruleMetadata.tag} onTagsChange={handleTagsChange} />
      <MalwareFamilySection families={ruleMetadata.malware_family} onFamiliesChange={handleFamiliesChange} />
    </Box>
  );
}

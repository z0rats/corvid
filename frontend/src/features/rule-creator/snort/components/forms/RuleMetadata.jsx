import React from 'react';
import { useTranslation } from 'react-i18next';
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
  const { t } = useTranslation('ruleCreator');
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
            label={t('snort.ruleMetadata.createdAtLabel')}
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
            label={t('snort.ruleMetadata.updatedAtLabel')}
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
            <InputLabel>{t('snort.ruleMetadata.policyLabel')}</InputLabel>
            <Select
              value={ruleMetadata.policy}
              label={t('snort.ruleMetadata.policyLabel')}
              onChange={(e) => handleChange('policy', e.target.value)}
            >
              <MenuItem value="">{t('common.none')}</MenuItem>
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
            <InputLabel>{t('snort.ruleMetadata.formerCategoryLabel')}</InputLabel>
            <Select
              value={ruleMetadata.former_category}
              label={t('snort.ruleMetadata.formerCategoryLabel')}
              onChange={(e) => handleChange('former_category', e.target.value)}
            >
              <MenuItem value="">{t('common.none')}</MenuItem>
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
            <InputLabel>{t('snort.ruleMetadata.signatureSeverityLabel')}</InputLabel>
            <Select
              value={ruleMetadata.signature_severity}
              label={t('snort.ruleMetadata.signatureSeverityLabel')}
              onChange={(e) => handleChange('signature_severity', e.target.value)}
            >
              <MenuItem value="">{t('common.none')}</MenuItem>
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
              <TextField {...params} label={t('snort.ruleMetadata.attackTargetLabel')} placeholder={t('snort.ruleMetadata.attackTargetPlaceholder')} size="small" />
            )}
            renderTags={(value, getTagProps) =>
              value.map((option, index) => {
                const { key, ...tagProps } = getTagProps({ index });
                return <Chip key={key} variant="outlined" label={option} size="small" {...tagProps} />;
              })
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
              <TextField {...params} label={t('snort.ruleMetadata.deploymentLabel')} placeholder={t('snort.ruleMetadata.deploymentPlaceholder')} size="small" />
            )}
            renderTags={(value, getTagProps) =>
              value.map((option, index) => {
                const { key, ...tagProps } = getTagProps({ index });
                return <Chip key={key} variant="outlined" label={option} size="small" {...tagProps} />;
              })
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

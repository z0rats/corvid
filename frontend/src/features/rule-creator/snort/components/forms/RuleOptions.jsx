import React from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import TextField from '@mui/material/TextField';
import Grid from '@mui/material/Grid';
import { SNORT_CONSTANTS } from '../../constants/snortConstants';
import ReferencesSection from './ReferencesSection';
import BasicMetadataSection from './BasicMetadataSection';

export default function RuleOptions({ ruleOptions, handleRuleOptionsChange }) {
  const { t } = useTranslation('ruleCreator');
  const handleChange = (field, value) => {
    handleRuleOptionsChange(prev => ({ ...prev, [field]: value }));
  };

  const handleReferencesChange = (newReferences) => {
    handleRuleOptionsChange(prev => ({ ...prev, reference: newReferences }));
  };

  const handleMetadataChange = (newMetadata) => {
    handleRuleOptionsChange(prev => ({ ...prev, metadata: newMetadata }));
  };

  return (
    <Box>
      <Grid container spacing={2}>
        <Grid size={12}>
          <TextField
            fullWidth
            label={t('snort.ruleOptions.messageLabel')}
            value={ruleOptions.msg}
            onChange={(e) => handleChange('msg', e.target.value)}
            required
            size="small"
            variant="outlined"
            placeholder={t('snort.ruleOptions.messagePlaceholder')}
          />
        </Grid>

        <Grid size={{ xs: 6, sm: 4 }}>
          <TextField
            fullWidth
            label={t('snort.ruleOptions.sidLabel')}
            value={ruleOptions.sid}
            onChange={(e) => handleChange('sid', e.target.value)}
            required
            size="small"
            variant="outlined"
            type="number"
            placeholder={t('snort.ruleOptions.sidPlaceholder')}
          />
        </Grid>

        <Grid size={{ xs: 6, sm: 4 }}>
          <TextField
            fullWidth
            label={t('snort.ruleOptions.revisionLabel')}
            value={ruleOptions.rev}
            onChange={(e) => handleChange('rev', e.target.value)}
            size="small"
            variant="outlined"
            type="number"
            placeholder={t('snort.ruleOptions.revisionPlaceholder')}
          />
        </Grid>

        <Grid size={{ xs: 6, sm: 4 }}>
          <TextField
            fullWidth
            label={t('snort.ruleOptions.priorityLabel')}
            value={ruleOptions.priority}
            onChange={(e) => handleChange('priority', e.target.value)}
            size="small"
            variant="outlined"
            type="number"
            placeholder={t('snort.ruleOptions.priorityPlaceholder')}
          />
        </Grid>

        <Grid size={{ xs: 12, sm: 6 }}>
          <FormControl fullWidth size="small">
            <InputLabel>{t('snort.ruleOptions.classTypeLabel')}</InputLabel>
            <Select
              value={ruleOptions.classtype}
              label={t('snort.ruleOptions.classTypeLabel')}
              onChange={(e) => handleChange('classtype', e.target.value)}
            >
              <MenuItem value="">{t('common.none')}</MenuItem>
              {SNORT_CONSTANTS.CLASSTYPES.map((classtype) => (
                <MenuItem key={classtype} value={classtype}>
                  {classtype}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
      </Grid>

      <ReferencesSection
        references={ruleOptions.reference}
        onReferencesChange={handleReferencesChange}
      />

      <BasicMetadataSection
        metadata={ruleOptions.metadata}
        onMetadataChange={handleMetadataChange}
      />
    </Box>
  );
}

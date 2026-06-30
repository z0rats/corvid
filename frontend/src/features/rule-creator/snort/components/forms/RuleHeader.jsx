import React from 'react';
import { useTranslation } from 'react-i18next';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import TextField from '@mui/material/TextField';
import Grid from '@mui/material/Grid';
import { SNORT_CONSTANTS } from '../../constants/snortConstants';

export default function RuleHeader({ ruleHeader, handleRuleHeaderChange }) {
  const { t } = useTranslation('ruleCreator');
  const handleChange = (field, value) => {
    handleRuleHeaderChange(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  return (
    <Grid container spacing={2}>
      <Grid size={{ xs: 12, sm: 6, md: 2 }}>
        <FormControl fullWidth size="small">
          <InputLabel>{t('snort.ruleHeader.actionLabel')}</InputLabel>
          <Select
            value={ruleHeader.action}
            label={t('snort.ruleHeader.actionLabel')}
            onChange={(e) => handleChange('action', e.target.value)}
          >
            {Object.values(SNORT_CONSTANTS.ACTIONS).map((action) => (
              <MenuItem key={action} value={action}>
                {action.toUpperCase()}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Grid>
      
      <Grid size={{ xs: 12, sm: 6, md: 2 }}>
        <FormControl fullWidth size="small">
          <InputLabel>{t('snort.ruleHeader.protocolLabel')}</InputLabel>
          <Select
            value={ruleHeader.protocol}
            label={t('snort.ruleHeader.protocolLabel')}
            onChange={(e) => handleChange('protocol', e.target.value)}
          >
            {Object.values(SNORT_CONSTANTS.PROTOCOLS).map((protocol) => (
              <MenuItem key={protocol} value={protocol}>
                {protocol.toUpperCase()}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Grid>

      <Grid size={{ xs: 6, sm: 3, md: 2 }}>
        <TextField
          fullWidth
          label={t('snort.ruleHeader.sourceIpLabel')}
          value={ruleHeader.sourceIP}
          onChange={(e) => handleChange('sourceIP', e.target.value)}
          size="small"
          variant="outlined"
          placeholder="any, !192.168.1.0/24"
        />
      </Grid>

      <Grid size={{ xs: 6, sm: 3, md: 1 }}>
        <TextField
          fullWidth
          label={t('snort.ruleHeader.sourcePortLabel')}
          value={ruleHeader.sourcePort}
          onChange={(e) => handleChange('sourcePort', e.target.value)}
          size="small"
          variant="outlined"
          placeholder="any, 80, !80"
        />
      </Grid>

      <Grid size={{ xs: 6, sm: 3, md: 1 }}>
        <FormControl fullWidth size="small">
          <InputLabel>{t('snort.ruleHeader.directionLabel')}</InputLabel>
          <Select
            value={ruleHeader.direction}
            label={t('snort.ruleHeader.directionLabel')}
            onChange={(e) => handleChange('direction', e.target.value)}
          >
            {Object.values(SNORT_CONSTANTS.DIRECTIONS).map((direction) => (
              <MenuItem key={direction} value={direction}>
                {direction}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Grid>

      <Grid size={{ xs: 6, sm: 3, md: 2 }}>
        <TextField
          fullWidth
          label={t('snort.ruleHeader.destIpLabel')}
          value={ruleHeader.destIP}
          onChange={(e) => handleChange('destIP', e.target.value)}
          size="small"
          variant="outlined"
          placeholder="any, $HOME_NET"
        />
      </Grid>

      <Grid size={{ xs: 6, sm: 3, md: 2 }}>
        <TextField
          fullWidth
          label={t('snort.ruleHeader.destPortLabel')}
          value={ruleHeader.destPort}
          onChange={(e) => handleChange('destPort', e.target.value)}
          size="small"
          variant="outlined"
          placeholder="any, 80, [80,443]"
        />
      </Grid>
    </Grid>
  );
}

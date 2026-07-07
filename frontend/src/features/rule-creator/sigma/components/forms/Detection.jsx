import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';

import { SIGMA_CONSTANTS } from '../../constants/sigmaConstants';
import KeywordsInput from './KeywordsInput';
import SelectionConditions from './SelectionConditions';

export default function Detection({
  detections,
  handleDetectionsChange,
  conditionsList,
  handleConditionsListChange,
}) {
  const { t } = useTranslation('ruleCreator');
  const [keywords, setKeywords] = useState([]);

  const handleAddKeyword = (keyword) => {
    setKeywords((prev) => [...prev, { id: crypto.randomUUID(), value: keyword }]);
  };

  const handleDeleteKeyword = (idToDelete) => {
    setKeywords((prev) => prev.filter((keyword) => keyword.id !== idToDelete));
  };

  const handleAddCondition = (condition) => {
    handleConditionsListChange((prev) => [...prev, condition]);
  };

  const handleDeleteCondition = (idToDelete) => {
    handleConditionsListChange((prev) => prev.filter((cond) => cond.id !== idToDelete));
  };

  return (
    <Box>
      <Typography variant="caption" sx={{ display: 'block' }} gutterBottom>
        {t('sigma.detection.helpNoSingleList')}
      </Typography>
      <Typography variant="caption" sx={{ display: 'block' }} gutterBottom>
        {t('sigma.detection.helpLowercase')}
      </Typography>
      <Typography variant="caption" sx={{ display: 'block' }} gutterBottom>
        {t('sigma.detection.helpComments')}
      </Typography>
      <Typography variant="caption" sx={{ display: 'block' }} gutterBottom>
        {t('sigma.detection.helpNoRegex')}
      </Typography>
      <Typography variant="caption" sx={{ display: 'block' }} gutterBottom>
        {t('sigma.detection.helpFieldNames')}
      </Typography>
      <Typography variant="caption" sx={{ display: 'block' }} gutterBottom>
        {t('sigma.detection.helpNoSiemLogic')}
      </Typography>

      {/* Keywords Section */}
      <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
        {t('sigma.detection.keywordsHeader')}
      </Typography>
      <KeywordsInput
        keywords={keywords}
        onAddKeyword={handleAddKeyword}
        onDeleteKeyword={handleDeleteKeyword}
      />

      {/* Selection Conditions Section */}
      <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
        {t('sigma.detection.selectionConditionsHeader')}
      </Typography>
      <SelectionConditions
        conditionsList={conditionsList}
        onAddCondition={handleAddCondition}
        onDeleteCondition={handleDeleteCondition}
      />

      {/* Filter and Timeframe */}
      <Grid container spacing={2} sx={{ mt: 2 }}>
        <Grid size={{ xs: 12, sm: 6 }}>
          <TextField
            fullWidth
            label={t('sigma.detection.filterLabel')}
            value={detections.filter}
            onChange={(e) =>
              handleDetectionsChange((prev) => ({ ...prev, filter: e.target.value }))
            }
            size="small"
            variant="outlined"
            placeholder={t('sigma.detection.filterPlaceholder')}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <TextField
            fullWidth
            label={t('sigma.detection.timeframeLabel')}
            value={detections.timeframe}
            onChange={(e) =>
              handleDetectionsChange((prev) => ({ ...prev, timeframe: e.target.value }))
            }
            size="small"
            variant="outlined"
            placeholder={t('sigma.detection.timeframePlaceholder')}
          />
        </Grid>
      </Grid>

      {/* Condition Selection */}
      {(conditionsList.length > 0 || keywords.length > 0 || detections.filter || detections.timeframe) && (
        <FormControl fullWidth size="small" sx={{ mt: 2 }}>
          <InputLabel>{t('sigma.detection.conditionLabel')}</InputLabel>
          <Select
            value={detections.condition}
            label={t('sigma.detection.conditionLabel')}
            onChange={(e) =>
              handleDetectionsChange((prev) => ({ ...prev, condition: e.target.value }))
            }
          >
            {SIGMA_CONSTANTS.CONDITIONS.map((condition) => (
              <MenuItem key={condition} value={condition}>
                {condition}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      )}
    </Box>
  );
}

import React from 'react';
import { useTranslation } from 'react-i18next';
import Autocomplete from '@mui/material/Autocomplete';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';

import logSourceData from '../../data/LogsourceData.json';

const categories = logSourceData.category;
const products = logSourceData.product;
const services = logSourceData.service;

export default function LogSource({ logSource, handleLogSourceChange }) {
  const { t } = useTranslation('ruleCreator');

  return (
    <Box>
      <Typography variant="subtitle2" gutterBottom>
        {t('sigma.logSource.helpText')}
      </Typography>
      <Grid container spacing={2} sx={{ mt: 1 }}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Grid container spacing={2} direction="column">
            <Grid size={12}>
              <Autocomplete
                freeSolo
                options={products}
                value={logSource.product}
                onChange={(event, newValue) => {
                  handleLogSourceChange((prev) => ({ ...prev, product: newValue || '' }));
                }}
                onInputChange={(event, newInputValue) => {
                  handleLogSourceChange((prev) => ({ ...prev, product: newInputValue }));
                }}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label={t('sigma.logSource.productLabel')}
                    placeholder={t('sigma.logSource.selectOrTypePlaceholder')}
                    size="small"
                    variant="outlined"
                    helperText={t('sigma.logSource.productHelper')}
                    fullWidth 
                  />
                )}
              />
            </Grid>
            <Grid size={12}>
              <Autocomplete
                freeSolo
                options={categories}
                value={logSource.category}
                onChange={(event, newValue) => {
                  handleLogSourceChange((prev) => ({ ...prev, category: newValue || '' }));
                }}
                onInputChange={(event, newInputValue) => {
                  handleLogSourceChange((prev) => ({ ...prev, category: newInputValue }));
                }}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label={t('sigma.logSource.categoryLabel')}
                    placeholder={t('sigma.logSource.selectOrTypePlaceholder')}
                    size="small"
                    variant="outlined"
                    helperText={t('sigma.logSource.categoryHelper')}
                    fullWidth
                  />
                )}
              />
            </Grid>
            <Grid size={12}>
              <Autocomplete
                freeSolo
                options={services}
                value={logSource.service}
                onChange={(event, newValue) => {
                  handleLogSourceChange((prev) => ({ ...prev, service: newValue || '' }));
                }}
                onInputChange={(event, newInputValue) => {
                  handleLogSourceChange((prev) => ({ ...prev, service: newInputValue }));
                }}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label={t('sigma.logSource.serviceLabel')}
                    placeholder={t('sigma.logSource.selectOrTypePlaceholder')}
                    size="small"
                    variant="outlined"
                    helperText={t('sigma.logSource.serviceHelper')}
                    fullWidth
                  />
                )}
              />
            </Grid>
          </Grid>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <TextField
            fullWidth
            label={t('sigma.logSource.definitionLabel')}
            value={logSource.definition}
            onChange={(e) =>
              handleLogSourceChange((prev) => ({ ...prev, definition: e.target.value }))
            }
            size="small"
            variant="outlined"
            placeholder={t('sigma.logSource.definitionPlaceholder')}
            multiline
            rows={7}
            helperText={t('sigma.logSource.definitionHelper')}
          />
        </Grid>
      </Grid>
    </Box>
  );
}

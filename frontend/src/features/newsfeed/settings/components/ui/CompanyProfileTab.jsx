import React from "react";
import { useTranslation } from "react-i18next";
import Box from '@mui/material/Box';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';

import { CTI_OPTIONS } from "../../../constants/newsfeedConstants";

export default function CompanyProfileTab({ ctiSettings, onInputChange, renderAutocomplete }) {
  const { t } = useTranslation('newsfeed');
  const profile = ctiSettings.company_profile || {};

  return (
    <Box sx={{ p: 1 }}>
      {renderAutocomplete(
        t('settings.cti.companyProfile.industrySelection'),
        CTI_OPTIONS.industries,
        profile.industry_selection,
        (e, newValue) => onInputChange("company_profile", "industry_selection", newValue),
        t('settings.cti.companyProfile.industrySelectionPlaceholder')
      )}
      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel>{t('settings.cti.companyProfile.companySize')}</InputLabel>
        <Select
          value={profile.company_size || ""}
          onChange={(e) => onInputChange("company_profile", "company_size", e.target.value)}
        >
          {CTI_OPTIONS.companySizes.map((size) => (
            <MenuItem key={size} value={size}>{size}</MenuItem>
          ))}
        </Select>
      </FormControl>
      {renderAutocomplete(
        t('settings.cti.companyProfile.geographicalScope'),
        CTI_OPTIONS.geographicalScopes,
        profile.geographical_scope,
        (e, newValue) => onInputChange("company_profile", "geographical_scope", newValue),
        t('settings.cti.companyProfile.geographicalScopePlaceholder')
      )}
      {renderAutocomplete(
        t('settings.cti.companyProfile.primaryLanguage'),
        CTI_OPTIONS.languages,
        profile.primary_language,
        (e, newValue) => onInputChange("company_profile", "primary_language", newValue),
        t('settings.cti.companyProfile.primaryLanguagePlaceholder')
      )}
      {renderAutocomplete(
        t('settings.cti.companyProfile.brandMentions'),
        [],
        profile.brand_mentions,
        (e, newValue) => onInputChange("company_profile", "brand_mentions", newValue),
        t('settings.cti.companyProfile.brandMentionsPlaceholder')
      )}
      {renderAutocomplete(
        t('settings.cti.companyProfile.competitorMonitoring'),
        [],
        profile.competitor_news_monitoring,
        (e, newValue) => onInputChange("company_profile", "competitor_news_monitoring", newValue),
        t('settings.cti.companyProfile.competitorMonitoringPlaceholder')
      )}
    </Box>
  );
}

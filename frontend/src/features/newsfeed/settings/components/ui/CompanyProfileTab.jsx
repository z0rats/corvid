import React from "react";
import Box from '@mui/material/Box';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';

import { CTI_OPTIONS } from "../../../constants/newsfeedConstants";

export default function CompanyProfileTab({ ctiSettings, onInputChange, renderAutocomplete }) {
  const profile = ctiSettings.company_profile || {};

  return (
    <Box sx={{ p: 1 }}>
      {renderAutocomplete(
        "Industry Selection",
        CTI_OPTIONS.industries,
        profile.industry_selection,
        (e, newValue) => onInputChange("company_profile", "industry_selection", newValue),
        "Add or select industries"
      )}
      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel>Company Size</InputLabel>
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
        "Geographical Scope",
        CTI_OPTIONS.geographicalScopes,
        profile.geographical_scope,
        (e, newValue) => onInputChange("company_profile", "geographical_scope", newValue),
        "Add or select regions"
      )}
      {renderAutocomplete(
        "Primary Language",
        CTI_OPTIONS.languages,
        profile.primary_language,
        (e, newValue) => onInputChange("company_profile", "primary_language", newValue),
        "Add or select languages"
      )}
      {renderAutocomplete(
        "Brand Mentions",
        [],
        profile.brand_mentions,
        (e, newValue) => onInputChange("company_profile", "brand_mentions", newValue),
        "Add brand names"
      )}
      {renderAutocomplete(
        "Competitor News Monitoring",
        [],
        profile.competitor_news_monitoring,
        (e, newValue) => onInputChange("company_profile", "competitor_news_monitoring", newValue),
        "Add competitor names"
      )}
    </Box>
  );
}

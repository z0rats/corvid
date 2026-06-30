import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import Autocomplete from '@mui/material/Autocomplete';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import Chip from '@mui/material/Chip';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import { useTheme } from "@mui/material/styles";

import { useCtiSettings } from "../hooks/api/useCtiSettingsApi";
import { useNotification } from "../../../core/hooks/ui/useNotification";
import NotificationSnackbar from "../components/ui/NotificationSnackbar";
import CompanyProfileTab from "./components/ui/CompanyProfileTab";
import ThreatActorTab from "./components/ui/ThreatActorTab";

export default function CTISettings() {
  const { t } = useTranslation('newsfeed');
  const theme = useTheme();
  const [tabIndex, setTabIndex] = useState(0);

  const {
    ctiSettings,
    loading,
    handleInputChange,
    handleAttackTypePriorityChange,
    saveSettings,
  } = useCtiSettings();

  const { notification, showSuccess, showError, hideNotification } = useNotification();

  const handleSave = async () => {
    const result = await saveSettings();
    if (result.success) {
      showSuccess(t('settings.cti.saveSuccess'));
    } else {
      showError(t('settings.cti.saveError'));
    }
  };

  const renderAutocomplete = (label, options, value, onChange, placeholder) => (
    <Autocomplete
      multiple
      freeSolo
      options={options}
      value={value || []}
      onChange={onChange}
      renderTags={(value, getTagProps) =>
        value.map((option, index) => {
          const { key, ...tagProps } = getTagProps({ index });
          return <Chip key={key} label={option} {...tagProps} />;
        })
      }
      renderInput={(params) => (
        <TextField {...params} label={label} placeholder={placeholder} />
      )}
      sx={{ mb: 2 }}
    />
  );

  return (
    <>
      <Card sx={{ p: 2, boxShadow: theme.shadows[1], borderRadius: 1 }}>
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6">{t('settings.cti.title')}</Typography>
          <Typography variant="body2" color="text.secondary">
            {t('settings.cti.description')}
          </Typography>
        </Box>
        <Tabs
          value={tabIndex}
          onChange={(e, newValue) => setTabIndex(newValue)}
          variant="scrollable"
          scrollButtons="auto"
          sx={{ borderBottom: 1, borderColor: "divider" }}
        >
          <Tab label={t('settings.cti.companyProfileTab')} />
          <Tab label={t('settings.cti.threatActorsTab')} />
        </Tabs>
        <Box sx={{ mt: 2 }}>
          {loading ? (
            <Typography>{t('settings.cti.loading')}</Typography>
          ) : (
            <>
              {tabIndex === 0 && (
                <CompanyProfileTab
                  ctiSettings={ctiSettings}
                  onInputChange={handleInputChange}
                  renderAutocomplete={renderAutocomplete}
                />
              )}
              {tabIndex === 1 && (
                <ThreatActorTab
                  ctiSettings={ctiSettings}
                  onInputChange={handleInputChange}
                  onAttackTypePriorityChange={handleAttackTypePriorityChange}
                  renderAutocomplete={renderAutocomplete}
                />
              )}
              <Box sx={{ textAlign: "left", mt: 2 }}>
                <Button variant="contained" color="primary" disableElevation onClick={handleSave}>
                  {t('settings.cti.saveSettings')}
                </Button>
              </Box>
            </>
          )}
        </Box>
      </Card>

      <NotificationSnackbar
        open={notification.open}
        message={notification.message}
        severity={notification.severity}
        onClose={hideNotification}
      />
    </>
  );
}

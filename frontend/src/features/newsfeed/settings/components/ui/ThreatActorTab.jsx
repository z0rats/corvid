import React from "react";
import { useTranslation } from "react-i18next";
import Box from '@mui/material/Box';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import Typography from '@mui/material/Typography';

import { CTI_OPTIONS } from "../../../constants/newsfeedConstants";

export default function ThreatActorTab({
  ctiSettings,
  onInputChange,
  onAttackTypePriorityChange,
  renderAutocomplete,
}) {
  const { t } = useTranslation('newsfeed');
  const threatConfig = ctiSettings.threat_actor_and_attack_type || {};

  return (
    <Box sx={{ p: 1 }}>
      {renderAutocomplete(
        t('settings.cti.threatActor.relevantThreatActors'),
        [],
        threatConfig.relevant_threat_actors,
        (e, newValue) => onInputChange("threat_actor_and_attack_type", "relevant_threat_actors", newValue),
        t('settings.cti.threatActor.relevantThreatActorsPlaceholder')
      )}
      {renderAutocomplete(
        t('settings.cti.threatActor.knownThreatActorNames'),
        [],
        threatConfig.known_threat_actor_names,
        (e, newValue) => onInputChange("threat_actor_and_attack_type", "known_threat_actor_names", newValue),
        t('settings.cti.threatActor.knownThreatActorNamesPlaceholder')
      )}
      {renderAutocomplete(
        t('settings.cti.threatActor.attackTypesOfInterest'),
        CTI_OPTIONS.attackTypes,
        threatConfig.attack_types_of_interest,
        (e, newValue) => onInputChange("threat_actor_and_attack_type", "attack_types_of_interest", newValue),
        t('settings.cti.threatActor.attackTypesOfInterestPlaceholder')
      )}

      {threatConfig.attack_types_of_interest?.map((attackType) => (
        <Box key={attackType} sx={{ display: "flex", alignItems: "center", mb: 1 }}>
          <Typography sx={{ mr: 2 }}>{attackType}</Typography>
          <FormControl variant="outlined" size="small" sx={{ minWidth: 120 }}>
            <InputLabel>{t('settings.cti.threatActor.priority')}</InputLabel>
            <Select
              value={threatConfig.attack_type_priorities?.[attackType] || ""}
              onChange={(e) => onAttackTypePriorityChange(attackType, e.target.value)}
              label={t('settings.cti.threatActor.priority')}
            >
              {CTI_OPTIONS.priorities.map((priority) => (
                <MenuItem key={priority} value={priority}>{priority}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
      ))}

      {renderAutocomplete(
        t('settings.cti.threatActor.motivationFilters'),
        CTI_OPTIONS.motivations,
        threatConfig.motivation_filters,
        (e, newValue) => onInputChange("threat_actor_and_attack_type", "motivation_filters", newValue),
        t('settings.cti.threatActor.motivationFiltersPlaceholder')
      )}
    </Box>
  );
}

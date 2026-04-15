import React from "react";
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
  const threatConfig = ctiSettings.threat_actor_and_attack_type || {};

  return (
    <Box sx={{ p: 1 }}>
      {renderAutocomplete(
        "Relevant Threat Actors",
        [],
        threatConfig.relevant_threat_actors,
        (e, newValue) => onInputChange("threat_actor_and_attack_type", "relevant_threat_actors", newValue),
        "Add threat actor names"
      )}
      {renderAutocomplete(
        "Known Threat Actor Names",
        [],
        threatConfig.known_threat_actor_names,
        (e, newValue) => onInputChange("threat_actor_and_attack_type", "known_threat_actor_names", newValue),
        "Add known threat actor names"
      )}
      {renderAutocomplete(
        "Attack Types of Interest",
        CTI_OPTIONS.attackTypes,
        threatConfig.attack_types_of_interest,
        (e, newValue) => onInputChange("threat_actor_and_attack_type", "attack_types_of_interest", newValue),
        "Add or select attack types"
      )}

      {threatConfig.attack_types_of_interest?.map((attackType) => (
        <Box key={attackType} sx={{ display: "flex", alignItems: "center", mb: 1 }}>
          <Typography sx={{ mr: 2 }}>{attackType}</Typography>
          <FormControl variant="outlined" size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Priority</InputLabel>
            <Select
              value={threatConfig.attack_type_priorities?.[attackType] || ""}
              onChange={(e) => onAttackTypePriorityChange(attackType, e.target.value)}
              label="Priority"
            >
              {CTI_OPTIONS.priorities.map((priority) => (
                <MenuItem key={priority} value={priority}>{priority}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
      ))}

      {renderAutocomplete(
        "Motivation Filters",
        CTI_OPTIONS.motivations,
        threatConfig.motivation_filters,
        (e, newValue) => onInputChange("threat_actor_and_attack_type", "motivation_filters", newValue),
        "Add or select motivations"
      )}
    </Box>
  );
}

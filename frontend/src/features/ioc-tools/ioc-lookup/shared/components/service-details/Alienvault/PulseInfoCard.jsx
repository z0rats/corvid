import React from "react";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Chip from "@mui/material/Chip";
import CircleIcon from "@mui/icons-material/Circle";
import Divider from "@mui/material/Divider";

import PolicyIcon from "@mui/icons-material/Policy";
import Typography from "@mui/material/Typography";

const getTlpColor = (tlpString) => {
  if (!tlpString) return 'action';
  switch (tlpString.toUpperCase()) {
    case 'RED': return 'error';
    case 'AMBER': return 'warning';
    case 'GREEN': return 'success';
    case 'BLUE': return 'info';
    case 'WHITE': return 'disabled';
    default: return 'action';
  }
};

export default function PulseInfoCard({ pulseInfo }) {
  const pulses = pulseInfo.count || 0;
  const uniquePulses = pulseInfo.pulses
    ? [...new Map(pulseInfo.pulses.map(p => [p.name, p])).values()]
    : [];

  return (
    <Card sx={{ borderRadius: 1, boxShadow: 0, height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <PolicyIcon />
          <Typography variant="h6" component="h2">Pulse Information</Typography>
        </Box>
        <Box sx={{ display: "flex", alignItems: "baseline", mt: 2, mb: pulses > 0 ? 1 : 0 }}>
          <Typography variant="h4" component="span" sx={{ mr: 1 }}>{pulses}</Typography>
          <Typography variant="subtitle1" component="span" color="text.secondary">
            {pulses === 1 ? "Pulse" : "Pulses"}
            {uniquePulses.length < pulses ? ` (${uniquePulses.length} unique)` : ''}
          </Typography>
        </Box>
        {uniquePulses.length > 0 && (
          <>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1" component="h3" gutterBottom sx={{ fontWeight: 'medium' }}>
              Referenced Pulses:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {uniquePulses.map((pulse) => (
                <Chip
                  key={pulse.id}
                  label={pulse.name}
                  icon={pulse.TLP ? <CircleIcon color={getTlpColor(pulse.TLP)} sx={{ fontSize: "1rem" }} /> : null}
                  size="small"
                  variant="outlined"
                />
              ))}
            </Box>
          </>
        )}
      </CardContent>
    </Card>
  );
}

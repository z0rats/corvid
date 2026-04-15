import React from "react";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Chip from "@mui/material/Chip";
import Box from "@mui/material/Box";

import CategoryIcon from "@mui/icons-material/CategoryOutlined";
import FingerprintIcon from "@mui/icons-material/FingerprintOutlined";
import InfoIcon from "@mui/icons-material/Info";
import LanguageIcon from "@mui/icons-material/LanguageOutlined";
import LocationOnIcon from "@mui/icons-material/LocationOnOutlined";
import ShieldIcon from "@mui/icons-material/ShieldOutlined";
import VerifiedIcon from "@mui/icons-material/VerifiedUserOutlined";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import Typography from "@mui/material/Typography";

const iconSx = { minWidth: 36 };

export default function GeneralInfoCard({ result }) {
  const location = [result.city, result.region, result.country_name].filter(Boolean).join(', ');

  return (
    <Card sx={{ borderRadius: 1, boxShadow: 0, height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <InfoIcon />
          <Typography variant="h6" component="h2">General Information</Typography>
        </Box>
        <List dense sx={{ mb: 1, mt: 1 }}>
          <ListItem disablePadding>
            <ListItemIcon sx={iconSx}><FingerprintIcon color="action" /></ListItemIcon>
            <ListItemText primary="Indicator" secondary={result.indicator || "N/A"} />
          </ListItem>
          {result.type && (
            <ListItem disablePadding>
              <ListItemIcon sx={iconSx}><CategoryIcon color="action" /></ListItemIcon>
              <ListItemText primary="Type" secondary={result.type} />
            </ListItem>
          )}
          {location && (
            <ListItem disablePadding>
              <ListItemIcon sx={iconSx}><LocationOnIcon color="action" /></ListItemIcon>
              <ListItemText primary="Location" secondary={location} />
            </ListItem>
          )}
          {result.asn && (
            <ListItem disablePadding>
              <ListItemIcon sx={iconSx}><LanguageIcon color="action" /></ListItemIcon>
              <ListItemText primary="ASN" secondary={result.asn} />
            </ListItem>
          )}
          {typeof result.reputation === 'number' && result.reputation !== 0 && (
            <ListItem disablePadding>
              <ListItemIcon sx={iconSx}><ShieldIcon color="action" /></ListItemIcon>
              <ListItemText primary="Reputation Score" secondary={String(result.reputation)} />
            </ListItem>
          )}
          {result.validation?.length > 0 && (
            <ListItem disablePadding>
              <ListItemIcon sx={iconSx}><VerifiedIcon color="action" /></ListItemIcon>
              <ListItemText
                primary="Validation"
                secondary={
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                    {result.validation.map((v, i) => (
                      <Chip key={i} label={v.name || v.message} size="small" />
                    ))}
                  </Box>
                }
              />
            </ListItem>
          )}
        </List>
      </CardContent>
    </Card>
  );
}

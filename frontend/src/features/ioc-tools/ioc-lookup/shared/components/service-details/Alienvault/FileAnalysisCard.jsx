import React from "react";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Box from "@mui/material/Box";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import ScienceIcon from "@mui/icons-material/Science";
import Typography from "@mui/material/Typography";

export default function FileAnalysisCard({ analysis }) {
  const info = analysis.analysis || {};

  return (
    <Card sx={{ mb: 2, borderRadius: 1, boxShadow: 0 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ScienceIcon />
          <Typography variant="h6" component="h2">File Analysis</Typography>
        </Box>
        <List dense sx={{ mt: 1 }}>
          {info.info?.results?.file_type && (
            <ListItem disablePadding>
              <ListItemText primary="File Type" secondary={info.info.results.file_type} />
            </ListItem>
          )}
          <ListItem disablePadding>
            <ListItemText primary="Status" secondary={analysis.analysis_status || info.status || "Unknown"} />
          </ListItem>
          {info.malware?.family?.length > 0 && (
            <ListItem disablePadding>
              <ListItemText primary="Malware Family" secondary={info.malware.family.join(', ')} />
            </ListItem>
          )}
        </List>
      </CardContent>
    </Card>
  );
}

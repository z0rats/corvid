import React from "react";
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Chip from '@mui/material/Chip';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';

import { RISK_CHIP_COLORS } from "../../../constants/newsfeedConstants";

export default function AnalysisCard({ result, index }) {
  const { title, analysis } = result;

  return (
    <Card
      variant="outlined"
      sx={{ mb: 2, boxShadow: 3, borderRadius: 2, position: "relative" }}
    >
      <CardHeader
        title={
          <Typography variant="h6" component="div" sx={{ fontWeight: "bold", width: "80%" }}>
            {title}
          </Typography>
        }
        action={
          <Chip
            label={"Risk: " + analysis.Risk}
            color={RISK_CHIP_COLORS[analysis.Risk] || "default"}
            size="small"
            sx={{ position: "absolute", top: 8, right: 8, borderRadius: 1 }}
          />
        }
      />
      <CardContent sx={{ pt: 1 }}>
        <Typography variant="body2" gutterBottom>
          <strong>Summary:</strong> {analysis.Summary}
        </Typography>
        <Typography variant="body2" gutterBottom>
          <strong>Reason:</strong> {analysis["Analysis comment"]}
        </Typography>
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: "bold" }}>
            Possible Action Items:
          </Typography>
          <List dense>
            {(analysis["Action items"] || []).map((item) => (
              <ListItem key={item}>
                <ListItemText primary={`- ${item}`} />
              </ListItem>
            ))}
          </List>
        </Box>
        <Typography variant="body2" gutterBottom>
          <strong>Source:</strong> {analysis["Source"]}
        </Typography>
      </CardContent>
    </Card>
  );
}

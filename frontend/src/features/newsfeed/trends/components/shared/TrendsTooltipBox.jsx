import React from "react";
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

export default function TrendsTooltipBox({ title, lines }) {
  return (
    <Box bgcolor="background.paper" p={1.5} border={1} borderColor="divider" borderRadius={1}>
      <Typography variant="body2" color="text.primary" fontWeight="medium">{title}</Typography>
      {lines.map((line, index) => (
        <Typography key={index} variant={line.variant || "body2"} color={line.color || "text.secondary"}>
          {line.text}
        </Typography>
      ))}
    </Box>
  );
}

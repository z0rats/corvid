import React from "react";
import Avatar from '@mui/material/Avatar';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardHeader from '@mui/material/CardHeader';
import Typography from '@mui/material/Typography';

export default function RankingCard({ article, index }) {
  return (
    <Card variant="outlined" sx={{ mb: 2 }}>
      <CardHeader
        title={
          <Box sx={{ display: "flex", alignItems: "center" }}>
            <Avatar>{index + 1}</Avatar>
            <Box sx={{ ml: 1 }}>
              <Typography variant="h6" component="div" sx={{ fontWeight: "bold" }}>
                {article.title}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Reason: {article.reason}
              </Typography>
            </Box>
          </Box>
        }
      />
    </Card>
  );
}

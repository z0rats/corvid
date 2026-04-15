import React from "react";
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Chip from '@mui/material/Chip';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import FindInPageIcon from '@mui/icons-material/FindInPage';

export default function KeywordsSection({ item }) {
  if (!item.matches || item.matches.length === 0) {
    return null;
  }

  return (
    <Accordion variant="secondary" sx={{borderRadius: 1}} >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        sx={{ flexDirection: "row-reverse" }} 
      >
        <Stack direction="row" alignItems="center" spacing={1}>
          <FindInPageIcon />
          <Typography variant="subtitle1" sx={{ fontWeight: "bold" }}>
            Keyword Match
            {item.matches.length > 1 ? "es " : " "}
            ({item.matches.length})
          </Typography>
        </Stack>
      </AccordionSummary>
      <AccordionDetails>
        <Stack direction="row" spacing={1} flexWrap="wrap">
          {item.matches.map((keyword) => (
            <Chip
              key={keyword}
              label={keyword}
              color="primary"
              sx={{ mb: 1 }}
            />
          ))}
        </Stack>
      </AccordionDetails>
    </Accordion>
  );
}
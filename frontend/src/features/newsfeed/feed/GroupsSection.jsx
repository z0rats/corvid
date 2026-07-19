import React from "react";
import { useTranslation } from "react-i18next";
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Chip from '@mui/material/Chip';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import ExpandMoreIcon from "@mui/icons-material/ExpandMoreOutlined";
import FindInPageIcon from '@mui/icons-material/FindInPage';

export default function GroupsSection({ item }) {
  const { t } = useTranslation('newsfeed');

  if (!item.matches || item.matches.length === 0) {
    return null;
  }

  return (
    <Accordion sx={(theme) => ({ border: 'none', boxShadow: 'none', bgcolor: theme.palette.grey[900] })} >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        sx={{ flexDirection: "row-reverse" }} 
      >
        <Stack direction="row" alignItems="center" spacing={1}>
          <FindInPageIcon />
          <Typography variant="subtitle1" sx={{ fontWeight: "bold" }}>
            {item.matches.length > 1 ? t('feed.groups.titlePlural') : t('feed.groups.title')}
            {" "}
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
              variant="outlined" 
              sx={{
                mb: 1,
              }}
            />
          ))}
        </Stack>
      </AccordionDetails>
    </Accordion>
  );
}
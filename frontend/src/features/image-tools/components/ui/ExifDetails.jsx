import React from 'react';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { imageUtils } from '../../utils/imageUtils';

export default function ExifDetails({ exif }) {
  const groups = imageUtils.groupExifTags(exif);
  const categories = Object.keys(groups);

  if (categories.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        No EXIF data found in this image.
      </Typography>
    );
  }

  return (
    <Box>
      {categories.map((category) => (
        <Accordion key={category} disableGutters sx={{ '&:before': { display: 'none' } }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="body2" fontWeight="medium">{category}</Typography>
          </AccordionSummary>
          <AccordionDetails>
            {Object.entries(groups[category]).map(([label, value]) => (
              <Box key={label} sx={{ display: 'flex', py: 0.5, gap: 2 }}>
                <Typography variant="body2" color="text.secondary" sx={{ minWidth: 180, flexShrink: 0 }}>
                  {label}
                </Typography>
                <Typography variant="body2" sx={{ wordBreak: 'break-all', flex: 1 }}>
                  {value}
                </Typography>
              </Box>
            ))}
          </AccordionDetails>
        </Accordion>
      ))}
    </Box>
  );
}

import React, { useState } from 'react';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import InfoIcon from '@mui/icons-material/Info';
import PlaceIcon from '@mui/icons-material/Place';
import ImageSearchIcon from '@mui/icons-material/ImageSearch';
import ImagePreview from './ImagePreview';
import FileMetadata from './FileMetadata';
import ExifDetails from './ExifDetails';
import GpsMap from './GpsMap';
import ReverseSearchLinks from './ReverseSearchLinks';

function Section({ icon, title, defaultExpanded, children }) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  return (
    <Accordion expanded={expanded} onChange={() => setExpanded(!expanded)} sx={{ mt: 2 }}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ minHeight: '48px', padding: '0 16px' }}>
        <Box display="flex" alignItems="center">
          {icon}
          <Typography variant="subtitle1" fontWeight="medium" sx={{ ml: 1 }}>{title}</Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ px: 2, py: 1 }}>
        {children}
      </AccordionDetails>
    </Accordion>
  );
}

export default function ImageAnalysisResult({ result, previewUrl, imageUrl }) {
  if (!result) {
    return null;
  }

  return (
    <>
      <ImagePreview previewUrl={previewUrl} fileInfo={result.file_info} />

      <Section icon={<InfoIcon />} title="General information" defaultExpanded>
        <FileMetadata fileInfo={result.file_info} hashes={result.hashes} />
      </Section>

      <Section icon={<PlaceIcon />} title="GPS location" defaultExpanded={Boolean(result.gps)}>
        <GpsMap gps={result.gps} />
      </Section>

      <Section icon={<InfoIcon />} title="EXIF metadata" defaultExpanded>
        <ExifDetails exif={result.exif} />
      </Section>

      <Section icon={<ImageSearchIcon />} title="Reverse image search" defaultExpanded>
        <ReverseSearchLinks imageUrl={imageUrl} />
      </Section>
    </>
  );
}

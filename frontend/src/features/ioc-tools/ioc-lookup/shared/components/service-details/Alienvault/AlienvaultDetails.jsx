import React from "react";
import Box from "@mui/material/Box";
import Grid from "@mui/material/Grid";
import NoDetails from "../NoDetails";
import GeneralInfoCard from "./GeneralInfoCard";
import PulseInfoCard from "./PulseInfoCard";
import MalwareSamplesCard from "./MalwareSamplesCard";
import FileAnalysisCard from "./FileAnalysisCard";

export default function AlienvaultDetails({ result }) {
  if (!result || result.error) {
    return <NoDetails message="Detailed information for AlienVault OTX is unavailable or still loading." />;
  }

  return (
    <Box sx={{ margin: 1 }}>
      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 6 }}>
          <GeneralInfoCard result={result} />
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          {result.pulse_info && <PulseInfoCard pulseInfo={result.pulse_info} />}
        </Grid>
        {result.section_malware?.data?.length > 0 && (
          <Grid size={{ xs: 12 }}>
            <MalwareSamplesCard malware={result.section_malware} />
          </Grid>
        )}
        {result.type === 'file' && result.section_analysis && (
          <Grid size={{ xs: 12 }}>
            <FileAnalysisCard analysis={result.section_analysis} />
          </Grid>
        )}
      </Grid>
    </Box>
  );
}

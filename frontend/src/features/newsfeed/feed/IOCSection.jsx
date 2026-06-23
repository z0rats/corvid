import React from "react";
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";

import { IOC_TYPES } from "../constants/newsfeedConstants";
import { parseIOCs } from "../utils/iocParser";

export default function IOCSection({ item }) {
  const parsedIOCs = parseIOCs(item.iocs);

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text);
  };

  const hasIOCs = IOC_TYPES.some(
    (ioc) => (parsedIOCs[ioc.type] || []).length > 0
  );

  if (!item.iocs || !hasIOCs) return null;

  return (
    <>
      {IOC_TYPES.map((ioc) => {
        const iocValues = parsedIOCs[ioc.type] || [];
        if (iocValues.length === 0) return null;

        return (
          <Accordion key={ioc.type} variant="secondary" sx={{ borderRadius: 1 }}>
            <AccordionSummary
              expandIcon={<ExpandMoreIcon />}
              sx={{
                "& .MuiAccordionSummary-content": { margin: 0 },
                flexDirection: "row-reverse",
                justifyContent: "space-between",
              }}
            >
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  width: "100%",
                }}
              >
                <Stack direction="row" alignItems="center" spacing={1}>
                  {ioc.icon}
                  <Typography variant="subtitle1" sx={{ fontWeight: "bold" }}>
                    {ioc.label} ({iocValues.length})
                  </Typography>
                </Stack>
                <Tooltip title="Copy All" arrow>
                  <IconButton
                    component="span"
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCopy(iocValues.join("\n"));
                    }}
                    aria-label="Copy All"
                    sx={{ mr: 1 }}
                  >
                    <ContentCopyIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>
            </AccordionSummary>
            <AccordionDetails sx={{ p: 2 }}>
              <Grid container spacing={1}>
                {iocValues.map((value) => (
                  <Grid size={{ xs: 12, sm: 6, md: 4, lg: 3 }} key={value}>
                    <Stack direction="row" alignItems="center" spacing={1}>
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleCopy(value);
                        }}
                      >
                        <Tooltip title="Copy">
                          <ContentCopyIcon />
                        </Tooltip>
                      </IconButton>
                      <Typography variant="body2">{value}</Typography>
                    </Stack>
                  </Grid>
                ))}
              </Grid>
            </AccordionDetails>
          </Accordion>
        );
      })}
    </>
  );
}

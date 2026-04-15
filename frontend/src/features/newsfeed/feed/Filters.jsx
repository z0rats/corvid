import React, { useState } from "react";
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Button from '@mui/material/Button';
import Checkbox from '@mui/material/Checkbox';
import CircularProgress from '@mui/material/CircularProgress';
import FormControl from '@mui/material/FormControl';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormGroup from '@mui/material/FormGroup';
import IconButton from '@mui/material/IconButton';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import TuneIcon from "@mui/icons-material/Tune";
import RefreshIcon from "@mui/icons-material/Refresh";
import DownloadIcon from "@mui/icons-material/Download";
import RestartAltIcon from "@mui/icons-material/RestartAlt";
import Grid from '@mui/material/Grid2';

import { newsfeedApi } from "../services/api/newsfeedApi";
import { TLP_OPTIONS } from "../constants/newsfeedConstants";
import { createLogger } from "../../../core/utils/logger";

const logger = createLogger("NewsfeedFilters");

export default function Filters({ filters, setFilters, applyFilters, resetFilters, refreshData }) {
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (event) => {
    const { name, value, checked, type } = event.target;
    setFilters({
      ...filters,
      [name]: type === "checkbox" ? (checked ? checked : null) : value,
    });
  };

  const handleRefresh = (event) => {
    event.stopPropagation();
    refreshData();
  };

  const handleFetchAndGet = async () => {
    setIsLoading(true);
    try {
      await newsfeedApi.fetchAndGetNews();
      refreshData();
    } catch (error) {
      logger.error("Error fetching news:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Accordion variant="secondary" sx={{ borderRadius: 1, border: "none" }}>
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        sx={{
          "& .MuiAccordionSummary-content": {
            justifyContent: "space-between",
            width: "100%",
          },
        }}
      >
        <Stack direction="row" alignItems="center" spacing={1} sx={{ flexGrow: 1 }}>
          <TuneIcon />
          <Typography variant="subtitle1" sx={{ fontWeight: "bold" }}>
            Advanced Options
          </Typography>
        </Stack>
        <Tooltip title="Refresh Feed">
          <IconButton
            component="div"
            role="button"
            tabIndex={0}
            size="small"
            onClick={handleRefresh}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleRefresh(e); }}
            aria-label="Refresh"
            sx={(theme) => ({ ml: 1, mr: 1, "&:hover": { backgroundColor: theme.palette.grey[200] } })}
          >
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </AccordionSummary>
      <AccordionDetails>
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 4 }}>
            <TextField
              label="Start Date"
              type="date"
              name="start_date"
              value={filters.start_date}
              onChange={handleChange}
              slotProps={{ inputLabel: { shrink: true } }}
              fullWidth
            />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <TextField
              label="End Date"
              type="date"
              name="end_date"
              value={filters.end_date}
              onChange={handleChange}
              slotProps={{ inputLabel: { shrink: true } }}
              fullWidth
            />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <FormControl fullWidth>
              <InputLabel id="tlp-label">TLP</InputLabel>
              <Select labelId="tlp-label" name="tlp" value={filters.tlp} label="TLP" onChange={handleChange}>
                {TLP_OPTIONS.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid size={{ xs: 12, md: 4 }}>
            <FormGroup>
              <FormControlLabel
                control={<Checkbox checked={filters.has_matches === true} onChange={handleChange} name="has_matches" />}
                label="Has Keyword Matches"
              />
              <FormControlLabel
                control={<Checkbox checked={filters.has_iocs === true} onChange={handleChange} name="has_iocs" />}
                label="Has IOCs"
              />
            </FormGroup>
          </Grid>

          <Grid size={{ xs: 12, md: 4 }}>
            <FormGroup>
              <FormControlLabel
                control={<Checkbox checked={filters.has_analysis === true} onChange={handleChange} name="has_analysis" />}
                label="Has Analysis"
              />
              <FormControlLabel
                control={<Checkbox checked={filters.has_note === true} onChange={handleChange} name="has_note" />}
                label="Has Note"
              />
            </FormGroup>
          </Grid>

          <Grid size={{ xs: 12, md: 4 }} sx={{ display: "flex", alignItems: "center" }}>
            <Stack direction="row" spacing={2}>
              <Button variant="outlined" color="inherit" startIcon={<RestartAltIcon />} onClick={resetFilters}>
                Reset Filters
              </Button>
              <Button
                variant="outlined"
                color="inherit"
                startIcon={isLoading ? null : <DownloadIcon />}
                onClick={handleFetchAndGet}
                disabled={isLoading}
              >
                {isLoading && <CircularProgress size={24} color="inherit" sx={{ mr: 1 }} />}
                {isLoading ? "Fetching..." : "Fetch News"}
              </Button>
            </Stack>
          </Grid>
        </Grid>
      </AccordionDetails>
    </Accordion>
  );
}

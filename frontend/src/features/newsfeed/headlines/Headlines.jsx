import React from "react";
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import FormControl from '@mui/material/FormControl';
import IconButton from '@mui/material/IconButton';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Paper from '@mui/material/Paper';
import Select from '@mui/material/Select';
import Stack from '@mui/material/Stack';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TablePagination from '@mui/material/TablePagination';
import TableRow from '@mui/material/TableRow';
import TableSortLabel from '@mui/material/TableSortLabel';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import RefreshIcon from "@mui/icons-material/Refresh";
import LaunchIcon from "@mui/icons-material/Launch";

import { useHeadlines } from "../hooks/api/useHeadlinesApi";
import { formatDate } from "../utils/formatters";
import { TIME_RANGE_OPTIONS } from "../constants/newsfeedConstants";

const isValidUrl = (url) => /^https?:\/\//i.test(url);

export default function Headlines() {
  const {
    timeFilter,
    setTimeFilter,
    page,
    rowsPerPage,
    orderBy,
    order,
    sourceFilter,
    setSourceFilter,
    titleFilter,
    setTitleFilter,
    handleSort,
    handleChangePage,
    handleChangeRowsPerPage,
    handleRefresh,
    displayData,
    filteredCount,
  } = useHeadlines();

  return (
    <Box sx={{ width: "100%" }}>
      <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
        <TextField label="Filter Source" size="small" value={sourceFilter} onChange={(e) => setSourceFilter(e.target.value)} />
        <TextField label="Filter Title" size="small" value={titleFilter} onChange={(e) => setTitleFilter(e.target.value)} />
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Time Range</InputLabel>
          <Select value={timeFilter} label="Time Range" onChange={(e) => setTimeFilter(e.target.value)}>
            {TIME_RANGE_OPTIONS.map((range) => (
              <MenuItem key={range.value} value={range.value}>
                {range.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <Tooltip title="Refresh">
          <IconButton onClick={handleRefresh} aria-label="Refresh">
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Stack>

      <TableContainer component={Paper}>
        <Table sx={{ minWidth: 650 }}>
          <TableHead>
            <TableRow>
              <TableCell>
                <TableSortLabel active={orderBy === "feedname"} direction={orderBy === "feedname" ? order : "asc"} onClick={() => handleSort("feedname")}>
                  Source
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel active={orderBy === "title"} direction={orderBy === "title" ? order : "asc"} onClick={() => handleSort("title")}>
                  Title
                </TableSortLabel>
              </TableCell>
              <TableCell align="right">
                <TableSortLabel active={orderBy === "date"} direction={orderBy === "date" ? order : "asc"} onClick={() => handleSort("date")}>
                  Time
                </TableSortLabel>
              </TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {displayData.map((headline) => (
              <TableRow key={headline.id} hover>
                <TableCell>
                  <Chip label={headline.feedname} size="small" sx={{ bgcolor: "primary.main", color: "primary.contrastText", borderRadius: 1 }} />
                </TableCell>
                <TableCell>{headline.title}</TableCell>
                <TableCell align="right">{formatDate(headline.date)}</TableCell>
                <TableCell align="right">
                  <Tooltip title="Open source">
                    <IconButton
                      size="small"
                      onClick={() => {
                        if (isValidUrl(headline.url)) {
                          window.open(headline.url, "_blank", "noopener,noreferrer");
                        }
                      }}
                      disabled={!isValidUrl(headline.url)}
                      aria-label="Open article"
                    >
                      <LaunchIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        rowsPerPageOptions={[5, 10, 25, 50]}
        component="div"
        count={filteredCount}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
    </Box>
  );
}

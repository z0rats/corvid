import React from "react";
import { useState } from "react";
import ReactCountryFlag from "react-country-flag";
import { useDomainSearch } from "../../hooks/api/useDomainSearch";
import { domainUtils } from "../../utils/domainUtils";

import CircleIcon from "@mui/icons-material/Circle";
import Collapse from "@mui/material/Collapse";
import Grow from "@mui/material/Grow";
import IconButton from "@mui/material/IconButton";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import LinearProgress from "@mui/material/LinearProgress";
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TablePagination from '@mui/material/TablePagination';
import TableRow from '@mui/material/TableRow';
import { useTheme } from '@mui/material/styles';
import Details from "./Details";
import NoResults from "./NoResults";

function StatusIcon({ status }) {
  const color = domainUtils.getStatusColor(status);
  return status === null ? null : <CircleIcon sx={{ color, fontSize: "small" }} />;
}

function Row({ row }) {
  const theme = useTheme();
  const [open, setOpen] = useState(false);

  return (
    <>
      <TableRow
        sx={{ bgcolor: theme.palette.background.tablecell }}
      >
        <TableCell>
          <IconButton
            aria-label="expand row"
            size="small"
            onClick={() => setOpen(!open)}
          >
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        </TableCell>
        <TableCell>
          <ReactCountryFlag countryCode={row["page"]["country"]} />
          &nbsp;&nbsp;
          {row["task"]["domain"]}
        </TableCell>
        <TableCell>
          <StatusIcon status={row["page"]["status"]} />
          &nbsp;{row["page"]["status"]}
        </TableCell>
        <TableCell>
          {domainUtils.formatDate(row["task"]["time"])}
        </TableCell>
      </TableRow>

      <TableRow>
        <TableCell
          sx={{
            pb: 0,
            pt: 0,
            backgroundColor: 'background.detailArea',
            overflowWrap: "anywhere",
          }}
          colSpan={6}
        >
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Details section={row} />
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
}

export default function ResultTable(props) {
  const theme = useTheme();
  const { data: response, loading } = useDomainSearch(props.domain);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(15);

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  if (loading)
    return (
      <>
        <br />
        <LinearProgress />
        <br />
        <br />
      </>
    );
  if (!response) return null;

  const results = response.results || [];
  if (results.length === 0) {
    return <NoResults searchterm={props.domain} />;
  }

  return (
    <>
      <Grow in={true}>
        <TableContainer
          component={Paper}
          sx={{
            boxShadow: 0,
            borderRadius: 1,
          }}
        >
          <Table aria-label="result_table">
            <TableHead>
              <TableRow>
                <TableCell
                  sx={{ bgcolor: theme.palette.background.tableheader }}
                />
                <TableCell
                  sx={{
                    bgcolor: theme.palette.background.tableheader,
                    fontWeight: "bold",
                  }}
                >
                  Domain
                </TableCell>
                <TableCell
                  sx={{
                    bgcolor: theme.palette.background.tableheader,
                    fontWeight: "bold",
                  }}
                >
                  Status code
                </TableCell>
                <TableCell
                  sx={{
                    bgcolor: theme.palette.background.tableheader,
                    fontWeight: "bold",
                    textAlign: "left",
                  }}
                >
                  Found
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {results.length > 0 ? (
                results
                  .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  .map((section) => {
                    return <Row key={section["task"]["uuid"]} row={section} />;
                  })
              ) : (
                <TableRow>
                  <TableCell>No Data</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
          <TablePagination
            rowsPerPageOptions={[15, 25, 50, 75, 100]}
            component="div"
            count={results.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
          />
        </TableContainer>
      </Grow>
    </>
  );
}

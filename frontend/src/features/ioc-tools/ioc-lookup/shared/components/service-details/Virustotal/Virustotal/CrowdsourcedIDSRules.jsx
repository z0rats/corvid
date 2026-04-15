import React from "react";
import { useState } from "react";

import Card from "@mui/material/Card";
import Grid from "@mui/material/Grid2";
import RuleIcon from "@mui/icons-material/Rule";
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TablePagination from '@mui/material/TablePagination';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';

export default function CrowdsourcedIDSRules(props) {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(3);
  const theme = useTheme();

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  return (
    <Card
      key="tags_card"
      sx={{ m: 1, p: 2, borderRadius: 1, boxShadow: 0 }}
    >
      <Grid container alignItems="center">
        <Grid mr={1}>
          <RuleIcon />
        </Grid>
        <Grid>
          <Typography variant="h5" component="h2" gutterBottom>
            Crowdsourced IDS rules
          </Typography>
        </Grid>
      </Grid>
      <TableContainer
        component={Paper}
        sx={{
          boxShadow: 0,
          borderRadius: 1,
          border: 1,
          borderColor: theme.palette.background.tableborder,
        }}
      >
        <Table>
          <TableHead>
            <TableRow>
              <TableCell
                sx={{
                  bgcolor: theme.palette.background.tablecell,
                  fontWeight: "bold",
                }}
              >
                Rule category
              </TableCell>
              <TableCell
                sx={{
                  bgcolor: theme.palette.background.tablecell,
                  fontWeight: "bold",
                }}
              >
                Alert severity
              </TableCell>
              <TableCell
                sx={{
                  bgcolor: theme.palette.background.tablecell,
                  fontWeight: "bold",
                }}
              >
                Rule message
              </TableCell>
              <TableCell
                sx={{
                  bgcolor: theme.palette.background.tablecell,
                  fontWeight: "bold",
                }}
              >
                Rule raw
              </TableCell>
              <TableCell
                sx={{
                  bgcolor: theme.palette.background.tablecell,
                  fontWeight: "bold",
                }}
              >
                Rule url
              </TableCell>
              <TableCell
                sx={{
                  bgcolor: theme.palette.background.tablecell,
                  fontWeight: "bold",
                }}
              >
                Rule source
              </TableCell>
              <TableCell
                sx={{
                  bgcolor: theme.palette.background.tablecell,
                  fontWeight: "bold",
                }}
              >
                Rule ID
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {props.result["data"]["attributes"]["crowdsourced_ids_results"]
              .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              .map((result) => (
                <TableRow key={result.rule_id}>
                  <TableCell>{result.rule_category}</TableCell>
                  <TableCell
                    sx={{
                      bgcolor:
                        result.alert_severity === "high"
                          ? theme.palette.error.main
                          : result.alert_severity === "medium"
                          ? theme.palette.warning.main
                          : theme.palette.success.main,
                    }}
                  >
                    {result.alert_severity}
                  </TableCell>
                  <TableCell>{result.rule_msg}</TableCell>
                  <TableCell>{result.rule_raw}</TableCell>
                  <TableCell>{result.rule_url}</TableCell>
                  <TableCell>{result.rule_source}</TableCell>
                  <TableCell>{result.rule_id}</TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
        <TablePagination
          rowsPerPageOptions={[3, 5, 10, 25, 50, 100]}
          component="div"
          count={
            Object.entries(
              props.result["data"]["attributes"]["crowdsourced_ids_results"]
            ).length
          }
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </TableContainer>
    </Card>
  );
}

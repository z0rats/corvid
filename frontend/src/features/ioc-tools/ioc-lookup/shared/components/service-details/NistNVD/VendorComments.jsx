import React from "react";
import { useState } from "react";

import BusinessIcon from "@mui/icons-material/Business";
import Card from "@mui/material/Card";
import CommentIcon from "@mui/icons-material/Comment";
import Grid from "@mui/material/Grid2";
import InfoIcon from "@mui/icons-material/Info";
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import ScheduleIcon from "@mui/icons-material/Schedule";
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TablePagination from '@mui/material/TablePagination';
import TableRow from '@mui/material/TableRow';
import Typography from "@mui/material/Typography";
import { useTheme } from '@mui/material/styles';

export default function VendorComments(props) {
  const theme = useTheme();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(5);

  const tableContainerStyle = {
    boxShadow: 0,
    borderRadius: 5,
    border: 1,
    borderColor: theme.palette.background.tableborder,
    mb: 2,
  };

  const tableCellStyle = {
    bgcolor: theme.palette.background.tablecell,
    fontWeight: "bold",
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  return (
    <Card
      variant="outlined"
      key="references_card"
      sx={{ m: 1, p: 2, borderRadius: 5, boxShadow: 0 }}
    >
      <Typography variant="h5" gutterBottom component="div">
        Vendor Comments
      </Typography>
      <List>
        <ListItem>
          <ListItemIcon>
            <InfoIcon />
          </ListItemIcon>
          <ListItemText secondary="Official Vendor Comment for the CVE. NVD provides a service whereby organizations can submit Official Vendor Comments for CVE associated with their products. Organizations can use the service in a variety of ways. For example, they can provide configuration and remediation guidance, clarify vulnerability applicability, provide deeper vulnerability analysis, dispute third party vulnerability information, and explain vulnerability impact. Official Vendor Comments can be submitted to the NVD by email at nvd@nist.gov." />
        </ListItem>
      </List>
      <TableContainer component={Paper} sx={tableContainerStyle}>
        <Table sx={{ minWidth: 650 }} aria-label="simple table">
          <TableHead>
            <TableRow>
              <TableCell sx={tableCellStyle}>
                <Grid container direction={"row"}>
                  <BusinessIcon sx={{ mr: 1 }} />
                  <Typography variant="h7" gutterBottom component="div">
                    Organization
                  </Typography>
                </Grid>
              </TableCell>
              <TableCell sx={tableCellStyle}>
                <Grid container direction={"row"}>
                  <CommentIcon sx={{ mr: 1 }} />
                  <Typography variant="h7" gutterBottom component="div">
                    Comment
                  </Typography>
                </Grid>
              </TableCell>
              <TableCell sx={tableCellStyle}>
                <Grid container direction={"row"}>
                  <ScheduleIcon sx={{ mr: 1 }} />
                  <Typography variant="h7" gutterBottom component="div">
                    Last modified
                  </Typography>
                </Grid>
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {props.comments
              .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              .map((comment) => (
                <TableRow key={`${comment.organization}-${comment.lastModified}`}>
                  <TableCell>{comment.organization}</TableCell>
                  <TableCell>{comment.comment}</TableCell>
                  <TableCell>{comment.lastModified}</TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
        <TablePagination
          rowsPerPageOptions={[5, 10, 15]}
          component="div"
          count={props.comments.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </TableContainer>
    </Card>
  );
}

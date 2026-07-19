import React from "react";
import { useState } from "react";
import { useTranslation } from 'react-i18next';

import BusinessIcon from "@mui/icons-material/BusinessOutlined";
import Card from "@mui/material/Card";
import CommentIcon from "@mui/icons-material/CommentOutlined";
import Grid from "@mui/material/Grid";
import InfoIcon from "@mui/icons-material/InfoOutlined";
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import ScheduleIcon from "@mui/icons-material/ScheduleOutlined";
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
  const { t } = useTranslation('iocTools');
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
        {t('providers.nistnvd.vendorComments')}
      </Typography>
      <List>
        <ListItem>
          <ListItemIcon>
            <InfoIcon />
          </ListItemIcon>
          <ListItemText secondary={t('providers.nistnvd.vendorCommentsDisclaimer')} />
        </ListItem>
      </List>
      <TableContainer component={Paper} sx={tableContainerStyle}>
        <Table sx={{ minWidth: 650 }} aria-label={t('providers.nistnvd.simpleTable')}>
          <TableHead>
            <TableRow>
              <TableCell sx={tableCellStyle}>
                <Grid container direction={"row"}>
                  <BusinessIcon sx={{ mr: 1 }} />
                  <Typography variant="h7" gutterBottom component="div">
                    {t('providers.nistnvd.organization')}
                  </Typography>
                </Grid>
              </TableCell>
              <TableCell sx={tableCellStyle}>
                <Grid container direction={"row"}>
                  <CommentIcon sx={{ mr: 1 }} />
                  <Typography variant="h7" gutterBottom component="div">
                    {t('providers.nistnvd.comment')}
                  </Typography>
                </Grid>
              </TableCell>
              <TableCell sx={tableCellStyle}>
                <Grid container direction={"row"}>
                  <ScheduleIcon sx={{ mr: 1 }} />
                  <Typography variant="h7" gutterBottom component="div">
                    {t('providers.nistnvd.lastModified')}
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

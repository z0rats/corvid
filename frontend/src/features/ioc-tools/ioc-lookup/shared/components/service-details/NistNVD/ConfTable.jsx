import React, { useState } from "react";
import { useTranslation } from 'react-i18next';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TablePagination from '@mui/material/TablePagination';
import TableRow from '@mui/material/TableRow';
import { useTheme } from '@mui/material/styles';

export default function ConfTable(props) {
  const { t } = useTranslation('iocTools');
  const yes = t('providers.common.yes');
  const no = t('providers.common.no');
  const theme = useTheme();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(5);
  const cpeMatchLength = props.configuration.nodes
    .map((node) => node.cpeMatch)
    .reduce((acc, curr) => acc + curr.length, 0);

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
    <TableContainer component={Paper} sx={tableContainerStyle}>
      <Table sx={{ minWidth: 650 }} aria-label={t('providers.nistnvd.simpleTable')}>
        <TableHead>
          <TableRow>
            <TableCell sx={tableCellStyle}>{t('providers.nistnvd.vulnerable')}</TableCell>
            <TableCell sx={tableCellStyle}>{t('providers.nistnvd.criteria')}</TableCell>
            <TableCell sx={tableCellStyle}>{t('providers.nistnvd.versionFrom')}</TableCell>
            <TableCell sx={tableCellStyle}>{t('providers.nistnvd.versionTo')}</TableCell>
            <TableCell sx={tableCellStyle}>{t('providers.nistnvd.criteriaId')}</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {props.configuration.nodes.map((node, index) =>
            node.cpeMatch
              .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              .map((cpeMatch, index) => (
                <TableRow key={index}>
                  <TableCell>{cpeMatch.vulnerable ? yes : no}</TableCell>
                  <TableCell sx={{ whiteSpace: "pre-line" }}>
                    {cpeMatch.criteria}
                  </TableCell>
                  <TableCell>{cpeMatch.versionStartIncluding}</TableCell>
                  <TableCell>{cpeMatch.versionEndExcluding}</TableCell>
                  <TableCell>{cpeMatch.matchCriteriaId}</TableCell>
                </TableRow>
              ))
          )}
        </TableBody>
      </Table>
      <TablePagination
        rowsPerPageOptions={[5, 10, 25, 50, 100]}
        component="div"
        count={cpeMatchLength}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
    </TableContainer>
  );
}

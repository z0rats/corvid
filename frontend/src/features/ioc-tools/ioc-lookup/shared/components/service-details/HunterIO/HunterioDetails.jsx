import React, { useState } from "react";
import { useTranslation } from 'react-i18next';

import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Grid from "@mui/material/Grid";
import InfoIcon from "@mui/icons-material/Info";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import SourceIcon from "@mui/icons-material/Source";
import Link from '@mui/material/Link';
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

import NoDetails from "../NoDetails";

const DetailListItem = ({ primary, secondary, yes, no, notAvailable }) => (
  <ListItem dense disableGutters>
    <ListItemText
      primary={primary}
      secondary={typeof secondary === 'boolean' ? (secondary ? yes : no) : (secondary || notAvailable)}
      primaryTypographyProps={{ variant: 'body2', fontWeight: 'medium' }}
      secondaryTypographyProps={{ variant: 'body2', color: 'text.secondary' }}
    />
  </ListItem>
);

export default function HunterioDetails({ result, ioc }) {
  const { t } = useTranslation('iocTools');
  const notAvailable = t('providers.common.notAvailable');
  const yes = t('providers.common.yes');
  const no = t('providers.common.no');
  const theme = useTheme();

  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(5);

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  if (!result || !result.data) {
    const message = result && result.error
        ? t('providers.hunterio.errorFetching', { error: result.message || result.error })
        : t('providers.hunterio.unavailable');
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={message} />
      </Box>
    );
  }

  const hunterData = result.data;
  const sources = Array.isArray(hunterData.sources) ? hunterData.sources : [];

  return (
    <Box sx={{ margin: 1, mt:0 }}>
      <Grid container spacing={2}>
        {/* Verification Details Card */}
        <Grid size={{ xs: 12, md: 5 }}>
          <Card elevation={0} sx={{ borderRadius: 2, border: '1px solid', borderColor: 'divider', height: '100%' }}>
            <CardContent>
              <Grid direction="row" container spacing={1} alignItems="center" mb={1}>
                <InfoIcon color="action" />
                <Typography variant="h6" component="div" sx={{ ml: 1 }}>
                  {t('providers.hunterio.emailVerificationDetails')}
                </Typography>
              </Grid>
              <List dense>
                <DetailListItem primary={t('providers.hunterio.fields.queriedEmail')} secondary={hunterData.email || ioc} yes={yes} no={no} notAvailable={notAvailable} />
                <DetailListItem primary={t('providers.hunterio.fields.verificationResult')} secondary={hunterData.result} yes={yes} no={no} notAvailable={notAvailable} />
                <DetailListItem primary={t('providers.hunterio.fields.status')} secondary={hunterData.status} yes={yes} no={no} notAvailable={notAvailable} />
                <DetailListItem primary={t('providers.hunterio.fields.score')} secondary={hunterData.score} yes={yes} no={no} notAvailable={notAvailable} />
                <DetailListItem primary={t('providers.hunterio.fields.regexpValid')} secondary={hunterData.regexp} yes={yes} no={no} notAvailable={notAvailable} />
                <DetailListItem primary={t('providers.hunterio.fields.gibberish')} secondary={hunterData.gibberish} yes={yes} no={no} notAvailable={notAvailable} />
                <DetailListItem primary={t('providers.hunterio.fields.disposable')} secondary={hunterData.disposable} yes={yes} no={no} notAvailable={notAvailable} />
                <DetailListItem primary={t('providers.hunterio.fields.webmail')} secondary={hunterData.webmail} yes={yes} no={no} notAvailable={notAvailable} />
                <DetailListItem primary={t('providers.hunterio.fields.mxRecords')} secondary={hunterData.mx_records} yes={yes} no={no} notAvailable={notAvailable} />
                <DetailListItem primary={t('providers.hunterio.fields.smtpServer')} secondary={hunterData.smtp_server} yes={yes} no={no} notAvailable={notAvailable} />
                <DetailListItem primary={t('providers.hunterio.fields.smtpCheck')} secondary={hunterData.smtp_check} yes={yes} no={no} notAvailable={notAvailable} />
                <DetailListItem primary={t('providers.hunterio.fields.acceptAll')} secondary={hunterData.accept_all} yes={yes} no={no} notAvailable={notAvailable} />
                <DetailListItem primary={t('providers.hunterio.fields.block')} secondary={hunterData.block} yes={yes} no={no} notAvailable={notAvailable} />
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Sources Card */}
        <Grid size={{ xs: 12, md: 7 }}>
          <Card elevation={0} sx={{ borderRadius: 2, border: '1px solid', borderColor: 'divider', height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{flexGrow: 1, display: 'flex', flexDirection: 'column'}}>
              <Grid direction="row" container spacing={1} alignItems="center" mb={1}>
                <SourceIcon color="action" />
                <Typography variant="h6" component="div" sx={{ ml: 1 }}>
                  {t('providers.hunterio.sourcesCount', { count: sources.length })}
                </Typography>
              </Grid>
              <Typography variant="caption" color="text.disabled" sx={{ display: 'block' }} mb={2}>
                {t('providers.hunterio.sourcesHelper')}
              </Typography>
              {sources.length > 0 ? (
                <TableContainer
                  component={Paper}
                  elevation={0}
                  sx={{
                    border: '1px solid',
                    borderColor: theme.palette.divider,
                    borderRadius: 1,
                    flexGrow: 1
                  }}
                >
                  <Table stickyHeader size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ bgcolor: theme.palette.background.paper, fontWeight: "bold" }}>{t('providers.hunterio.columns.domain')}</TableCell>
                        <TableCell sx={{ bgcolor: theme.palette.background.paper, fontWeight: "bold" }}>{t('providers.hunterio.columns.uri')}</TableCell>
                        <TableCell sx={{ bgcolor: theme.palette.background.paper, fontWeight: "bold" }}>{t('providers.hunterio.columns.extracted')}</TableCell>
                        <TableCell sx={{ bgcolor: theme.palette.background.paper, fontWeight: "bold" }}>{t('providers.hunterio.columns.lastSeen')}</TableCell>
                        <TableCell sx={{ bgcolor: theme.palette.background.paper, fontWeight: "bold" }}>{t('providers.hunterio.columns.stillOnPage')}</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {sources
                        .slice(
                          page * rowsPerPage,
                          page * rowsPerPage + rowsPerPage
                        )
                        .map((source, index) => (
                          <TableRow hover key={source.uri + index}>
                            <TableCell sx={{wordBreak:'break-all'}}>{source.domain}</TableCell>
                            <TableCell sx={{wordBreak:'break-all'}}>
                                <Link href={source.uri} target="_blank" rel="noopener noreferrer" sx={{display:'block', maxWidth: 200, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap'}} title={source.uri}>
                                    {source.uri}
                                </Link>
                            </TableCell>
                            <TableCell>{source.extracted_on || notAvailable}</TableCell>
                            <TableCell>{source.last_seen_on || notAvailable}</TableCell>
                            <TableCell>{source.still_on_page ? yes : no}</TableCell>
                          </TableRow>
                        ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Typography sx={{textAlign:'center', mt:2}}>{t('providers.hunterio.noSourcesFound')}</Typography>
              )}
            </CardContent>
             {sources.length > 0 && (
                <TablePagination
                    rowsPerPageOptions={[5, 10, 25]}
                    component="div"
                    count={sources.length}
                    rowsPerPage={rowsPerPage}
                    page={page}
                    onPageChange={handleChangePage}
                    onRowsPerPageChange={handleChangeRowsPerPage}
                    sx={{ borderTop: `1px solid ${theme.palette.divider}`, flexShrink: 0 }}
                />
             )}
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

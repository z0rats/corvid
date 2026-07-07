import React, { useState } from "react";
import { useTranslation } from 'react-i18next';
import ContentPasteSearchIcon from "@mui/icons-material/ContentPasteSearch";
import LockOpenIcon from "@mui/icons-material/LockOpen";
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Divider from '@mui/material/Divider';
import Stack from '@mui/material/Stack';
import TablePagination from '@mui/material/TablePagination';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import NoDetails from "../NoDetails";

const filterResults = (array, term) => {
  if (!term) return array;
  return array.filter((item) =>
    Object.values(item).some((value) =>
      value
        ? value.toString().toLowerCase().includes(term.toLowerCase())
        : false
    )
  );
};

const paginate = (array, p, ipp) => {
  return array.slice(p * ipp, p * ipp + ipp);
};

const downloadTextFile = (data, filename) => {
  const blob = new Blob([data], { type: "text/plain;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(link.href);
};

const Breaches = ({ breaches, t, notAvailable }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(0);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  if (!breaches || breaches.length === 0) {
    return (
      <Card variant="outlined" sx={{ m: 1, p: 2, borderRadius: 2, boxShadow: 0, flexGrow: 1, border: '1px solid', borderColor: 'divider' }}>
        <Stack direction="row" spacing={1} alignItems="center" mb={1}>
          <LockOpenIcon />
          <Typography variant="h6">{t('providers.hibp.breaches')}</Typography>
        </Stack>
        <Typography>{t('providers.hibp.noBreachesFound')}</Typography>
      </Card>
    );
  }

  const handlePageChange = (event, newPage) => {
    setPage(newPage);
  };

  const handleItemsPerPageChange = (event) => {
    setItemsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleSearchChange = (event) => {
    setSearchTerm(event.target.value);
    setPage(0);
  };

  const downloadBreaches = () => {
    const breachText = filteredBreaches.map((account) => `${account.Name}`).join("\n");
    downloadTextFile(breachText, "breaches.txt");
  };

  const filteredBreaches = filterResults(breaches, searchTerm);
  const paginatedBreaches = paginate(filteredBreaches, page, itemsPerPage);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", flexGrow: 1, height: '100%' }}>
      <Card
        variant="outlined"
        sx={{
          m: 1,
          p: 2,
          borderRadius: 2,
          boxShadow: 0,
          flexGrow: 1,
          display: "flex",
          flexDirection: "column",
          border: '1px solid',
          borderColor: 'divider'
        }}
      >
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            mb:1
          }}
        >
          <Stack direction="row" spacing={1} alignItems="center">
            <LockOpenIcon />
            <Typography variant="h6">
              {t('providers.hibp.breachesCount', { count: filteredBreaches.length })}
            </Typography>
          </Stack>
          <TextField
            label={t('providers.hibp.searchBreaches')}
            variant="outlined"
            size="small"
            value={searchTerm}
            onChange={handleSearchChange}
            sx={{ borderRadius: "10px", "& .MuiOutlinedInput-root": { borderRadius: "10px" }, inputProps: {style: { padding: 8 }} }}
          />
        </Box>
        <Typography variant="caption" color="text.secondary" sx={{ mb: 2 }}>
          {t('providers.hibp.breachesHelper')}
        </Typography>
        <CardContent sx={{ flexGrow: 1, p:0, overflowY: 'auto' }}>
          {paginatedBreaches.length > 0 ? (
            paginatedBreaches.map((account) => (
              <Box key={account.Name || account.Title } mb={1} >
                {account.Name && (
                  <Typography variant="body1" component="div">
                    {account.Name}
                    {account.IsVerified && <Typography component="span" variant="caption" color="success.main" sx={{ml:1}}>{t('providers.hibp.verified')}</Typography>}
                  </Typography>
                )}
                 {account.Domain && <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>{t('providers.hibp.domain')} {account.Domain}</Typography>}
                <Divider sx={{ my: 0.5 }} />
              </Box>
            ))
          ) : (
            <Typography sx={{textAlign: 'center', mt: 2}}>{t('providers.hibp.noMatchingBreaches')}</Typography>
          )}
        </CardContent>
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            pt: 2,
            borderTop: '1px solid',
            borderColor: 'divider',
            mt: 'auto'
          }}
        >
          <Button
            variant="outlined"
            size="small"
            color="primary"
            onClick={downloadBreaches}
            disabled={filteredBreaches.length === 0}
          >
            {t('providers.hibp.exportList')}
          </Button>
          <TablePagination
            component="div"
            count={filteredBreaches.length}
            page={page}
            onPageChange={handlePageChange}
            rowsPerPage={itemsPerPage}
            onRowsPerPageChange={handleItemsPerPageChange}
            rowsPerPageOptions={[5, 10, 15, 25]}
            size="small"
          />
        </Box>
      </Card>
    </Box>
  );
};

const Pastes = ({ pastes, t, notAvailable }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(0);
  const [itemsPerPage, setItemsPerPage] = useState(5);

  if (!pastes || pastes.length === 0) {
     return (
      <Card variant="outlined" sx={{ m: 1, p: 2, borderRadius: 2, boxShadow: 0, flexGrow: 1, border: '1px solid', borderColor: 'divider' }}>
        <Stack direction="row" spacing={1} alignItems="center" mb={1}>
          <ContentPasteSearchIcon />
          <Typography variant="h6">{t('providers.hibp.pastes')}</Typography>
        </Stack>
        <Typography>{t('providers.hibp.noPastesFound')}</Typography>
      </Card>
    );
  }

  const handlePageChange = (event, newPage) => {
    setPage(newPage);
  };

  const handleItemsPerPageChange = (event) => {
    setItemsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleSearchChange = (event) => {
    setSearchTerm(event.target.value);
    setPage(0);
  };

  const downloadPastes = () => {
    const pasteText = filteredPastes
      .map(
        (paste) =>
          `Title: ${paste.Title || notAvailable}\nSource: ${paste.Source}\nDate: ${paste.Date ? new Date(paste.Date).toLocaleDateString() : notAvailable}\nEmailCount: ${paste.EmailCount}\n\n`
      )
      .join("\n");
    downloadTextFile(pasteText, "pastes.txt");
  };

  const filteredPastes = filterResults(pastes, searchTerm);
  const paginatedPastes = paginate(filteredPastes, page, itemsPerPage);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", flexGrow: 1, height: '100%' }}>
      <Card
        variant="outlined"
        sx={{
          m: 1,
          p: 2,
          borderRadius: 2,
          boxShadow: 0,
          flexGrow: 1,
          display: "flex",
          flexDirection: "column",
          border: '1px solid',
          borderColor: 'divider'
        }}
      >
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            mb: 1
          }}
        >
          <Stack direction="row" spacing={1} alignItems="center">
            <ContentPasteSearchIcon />
            <Typography variant="h6">
              {t('providers.hibp.pastesCount', { count: filteredPastes.length })}
            </Typography>
          </Stack>
          <TextField
            label={t('providers.hibp.searchPastes')}
            variant="outlined"
            size="small"
            value={searchTerm}
            onChange={handleSearchChange}
            sx={{ borderRadius: "10px", "& .MuiOutlinedInput-root": { borderRadius: "10px" }, inputProps: {style: { padding: 8 }} }}
          />
        </Box>
        <Typography variant="caption" color="text.secondary" sx={{ mb: 2 }}>
          {t('providers.hibp.pastesHelper')}
        </Typography>
        <CardContent sx={{ flexGrow: 1, p:0, overflowY: 'auto' }}>
          {paginatedPastes.length > 0 ? (
            paginatedPastes.map((paste) => (
              <Box key={paste.Id} mb={1}>
                <Tooltip title={paste.Title || t('providers.hibp.noTitleAvailable')}>
                    <Typography variant="subtitle1" noWrap sx={{fontWeight:'medium'}}>
                        {paste.Title || t('providers.hibp.noTitle')}
                    </Typography>
                </Tooltip>
                {paste.Source && (
                  <Typography variant="caption" sx={{ display: 'block' }}>
                    <b>{t('providers.hibp.source')}</b> {paste.Source}
                  </Typography>
                )}
                {paste.Date && (
                  <Typography variant="caption" sx={{ display: 'block' }}>
                    <b>{t('providers.hibp.date')}</b> {new Date(paste.Date).toLocaleDateString()}
                  </Typography>
                )}
                {typeof paste.EmailCount !== 'undefined' && (
                  <Typography variant="caption" sx={{ display: 'block' }}>
                    <b>{t('providers.hibp.emailCount')}</b> {paste.EmailCount}
                  </Typography>
                )}
                <Divider sx={{ my: 0.5 }} />
              </Box>
            ))
          ) : (
            <Typography sx={{textAlign: 'center', mt: 2}}>{t('providers.hibp.noMatchingPastes')}</Typography>
          )}
        </CardContent>
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            pt: 2,
            borderTop: '1px solid',
            borderColor: 'divider',
            mt: 'auto'
          }}
        >
          <Button
            variant="outlined"
            size="small"
            color="primary"
            onClick={downloadPastes}
            disabled={filteredPastes.length === 0}
          >
            {t('providers.hibp.exportList')}
          </Button>
          <TablePagination
            component="div"
            count={filteredPastes.length}
            page={page}
            onPageChange={handlePageChange}
            rowsPerPage={itemsPerPage}
            onRowsPerPageChange={handleItemsPerPageChange}
            rowsPerPageOptions={[3, 5, 10]}
            size="small"
          />
        </Box>
      </Card>
    </Box>
  );
};

export default function HaveibeenpwndDetails({ result, ioc }) {
  const { t } = useTranslation('iocTools');
  const notAvailable = t('providers.common.notAvailable');

  if (!result) {
     return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={t('providers.hibp.loading')} />
      </Box>
    );
  }

  if (result.error) {
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={t('providers.hibp.errorFetching', { error: result.message || result.error })} />
      </Box>
    );
  }

  const breaches = result.breachedaccount || [];
  const pastes = result.pasteaccount || [];

  if (breaches.length === 0 && pastes.length === 0) {
     return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={t('providers.hibp.noResultsFound', { ioc })} />
      </Box>
    );
  }

  return (
    <Box sx={{ margin: 1, mt:0 }}>
      <Grid container spacing={2} alignItems="stretch">
        {(breaches.length > 0 || pastes.length === 0) && (
            <Grid size={12} md={pastes.length> 0 ? 6 : 12} sx={{ display: "flex" }}>
                <Breaches breaches={breaches} t={t} notAvailable={notAvailable} />
            </Grid>
        )}
        {(pastes.length > 0 || breaches.length === 0) && (
            <Grid size={12} md={breaches.length> 0 ? 6 : 12} sx={{ display: "flex" }}>
                <Pastes pastes={pastes} t={t} notAvailable={notAvailable} />
            </Grid>
        )}
      </Grid>
    </Box>
  );
}

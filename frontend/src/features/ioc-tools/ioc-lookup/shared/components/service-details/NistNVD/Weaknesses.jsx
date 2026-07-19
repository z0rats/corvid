import React from "react";
import { useTranslation } from 'react-i18next';

import Card from "@mui/material/Card";
import CategoryIcon from "@mui/icons-material/CategoryOutlined";
import Grid from "@mui/material/Grid";
import InfoIcon from "@mui/icons-material/InfoOutlined";
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import NumbersIcon from "@mui/icons-material/NumbersOutlined";
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import SourceIcon from "@mui/icons-material/SourceOutlined";
import Typography from "@mui/material/Typography";
import { useTheme } from '@mui/material/styles';

export default function Weaknesses(props) {
  const { t } = useTranslation('iocTools');
  const theme = useTheme();
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

  return (
    <Card
      variant="outlined"
      key="weaknesses_card"
      sx={{ m: 1, p: 2, borderRadius: 5, boxShadow: 0 }}
    >
      <Typography variant="h5" gutterBottom component="div">
        {t('providers.nistnvd.weaknesses')}
      </Typography>
      <List>
        <ListItem>
          <ListItemIcon>
            <InfoIcon />
          </ListItemIcon>
          <ListItemText secondary={t('providers.nistnvd.weaknessesDisclaimer')} />
        </ListItem>
      </List>
      {props.details ? (
        <>
          <TableContainer component={Paper} sx={tableContainerStyle}>
            <Table sx={{ minWidth: 650 }} aria-label={t('providers.nistnvd.simpleTable')}>
              <TableHead>
                <TableRow>
                  <TableCell sx={tableCellStyle}>
                    <Grid container direction={"row"}>
                      <NumbersIcon sx={{ mr: 1 }} />
                      <Typography variant="h7" gutterBottom component="div">
                        CWE-ID
                      </Typography>
                    </Grid>
                  </TableCell>
                  <TableCell sx={tableCellStyle}>
                    <Grid container direction={"row"}>
                      <CategoryIcon sx={{ mr: 1 }} />
                      <Typography variant="h7" gutterBottom component="div">
                        {t('providers.common.type')}
                      </Typography>
                    </Grid>
                  </TableCell>
                  <TableCell sx={tableCellStyle}>
                    <Grid container direction={"row"}>
                      <SourceIcon sx={{ mr: 1 }} />
                      <Typography variant="h7" gutterBottom component="div">
                        {t('providers.nistnvd.source')}
                      </Typography>
                    </Grid>
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {props.weaknesses.map((weaknews) => (
                  <TableRow key={`${weaknews.description[0].value}-${weaknews.source}`}>
                    <TableCell> {weaknews.description[0].value} </TableCell>
                    <TableCell> {weaknews.type} </TableCell>
                    <TableCell> {weaknews.source} </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </>
      ) : null}
    </Card>
  );
}

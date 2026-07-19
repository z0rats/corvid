import React from "react";
import { useTranslation } from 'react-i18next';

import IocLookupDialog from '../../../ioc-lookup/shared/components/IocLookupDialog';
import { useIocLookupDialog } from '../../../ioc-lookup/shared/hooks/useIocLookupDialog';
import AdminPanelSettingsIcon from "@mui/icons-material/AdminPanelSettingsOutlined";
import Box from "@mui/material/Box";
import BusinessIcon from "@mui/icons-material/BusinessOutlined";
import Button from "@mui/material/Button";
import CalendarMonthIcon from "@mui/icons-material/CalendarMonthOutlined";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import CategoryIcon from "@mui/icons-material/CategoryOutlined";
import CircleIcon from "@mui/icons-material/CircleOutlined";
import DateRangeIcon from "@mui/icons-material/DateRangeOutlined";
import DomainVerificationIcon from "@mui/icons-material/DomainVerificationOutlined";
import Grid from "@mui/material/Grid";
import HttpIcon from "@mui/icons-material/HttpOutlined";
import LanIcon from "@mui/icons-material/LanOutlined";
import LanguageIcon from "@mui/icons-material/LanguageOutlined";
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import OpenInNewIcon from "@mui/icons-material/OpenInNewOutlined";
import Stack from "@mui/material/Stack";
import StorageIcon from "@mui/icons-material/StorageOutlined";
import Typography from "@mui/material/Typography";

function getStatusColor(status) {
  const statusStr = String(status);
  if (statusStr.startsWith('2')) return 'success.main';
  if (statusStr.startsWith('4')) return 'warning.main';
  if (statusStr.startsWith('5')) return 'error.main';
  return 'text.disabled';
}

export default function Details(props) {
  const { t } = useTranslation('iocTools');
  const { open, ioc, iocType, openDialog, closeDialog } = useIocLookupDialog();

  return (
    <Box sx={{ margin: 1 }}>
      <Card
        key={"screenshot_card_" + props.section["task"]["uuid"]}
        sx={{
          m: 1,
          p: 2,
          borderRadius: 1,
          boxShadow: 0,
          float: "right",
          height: "100%",
        }}
      >
        <Stack sx={{ float: "right" }}>
          <Typography variant="h6" align="center">
            {t('domainFinder.details.screenshot')}
          </Typography>
          {(props.section["task"]["screenshotURL"] || 
            props.section["screenshot"] || 
            props.section["task"]["screenshot"] ||
            (props.section["task"]["uuid"] && `https://urlscan.io/screenshots/${props.section["task"]["uuid"]}.png`)) ? (
            <a
              href={props.section["task"]["screenshotURL"] || 
                    props.section["screenshot"] || 
                    props.section["task"]["screenshot"] ||
                    `https://urlscan.io/screenshots/${props.section["task"]["uuid"]}.png`}
              target="_blank"
              rel="noopener noreferrer"
            >
              <Box
                component="img"
                src={props.section["task"]["screenshotURL"] ||
                     props.section["screenshot"] ||
                     props.section["task"]["screenshot"] ||
                     `https://urlscan.io/screenshots/${props.section["task"]["uuid"]}.png`}
                alt="Website screenshot"
                sx={{
                  width: 250,
                  float: 'right',
                  borderRadius: 1,
                }}
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.parentElement.style.display = 'none';
                }}
              />
            </a>
          ) : (
            <Typography variant="body2" color="text.secondary">
              {t('domainFinder.details.noScreenshot')}
            </Typography>
          )}
        </Stack>
      </Card>

      <Card
        sx={{
          m: 1,
          p: 1,
          borderRadius: 1,
          boxShadow: 0,
          height: "100%",
        }}
      >
        <CardContent>
          <Grid container spacing={2}>
            <Grid size={6}>
              <List>
                <ListItem>
                  <ListItemIcon>
                    <LanIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary={t('domainFinder.details.fields.ip')}
                    secondary={
                      props.section["page"]["ip"]
                        ? props.section["page"]["ip"]
                        : t('domainFinder.details.notAvailable')
                    }
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <LanguageIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary={t('domainFinder.details.fields.country')}
                    secondary={
                      props.section["page"]["country"]
                        ? props.section["page"]["country"]
                        : t('domainFinder.details.notAvailable')
                    }
                  />
                </ListItem>
              </List>
            </Grid>
            <Grid size={6}>
              <List>
                <ListItem>
                  <ListItemIcon>
                    <HttpIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary={t('domainFinder.details.fields.url')}
                    secondary={
                      props.section["page"]["url"]
                        ? props.section["page"]["url"]
                        : t('domainFinder.details.notAvailable')
                    }
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <OpenInNewIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary={t('domainFinder.details.fields.result')}
                    secondary={
                      props.section["result"] ? props.section["result"] : t('domainFinder.details.notAvailable')
                    }
                  />
                </ListItem>
              </List>
            </Grid>
          </Grid>
          <Button
            variant="outlined"
            disableElevation
            size="small"
            onClick={() => openDialog(props.section["page"]["ip"], 'IPv4')}
          >
            {t('domainFinder.details.actions.analyzeIp')}
          </Button>
          &nbsp;&nbsp;
          <Button
            variant="outlined"
            disableElevation
            size="small"
            onClick={() => openDialog(props.section["task"]["domain"], 'Domain')}
          >
            {t('domainFinder.details.actions.analyzeDomain')}
          </Button>
        </CardContent>
      </Card>

      <Card
        sx={{ m: 1, p: 1, borderRadius: 1, boxShadow: 0 }}
      >
        <CardContent>
          <Grid container spacing={2}>
            <Grid size={6}>
              <List>
                <ListItem>
                  <ListItemIcon>
                    <CircleIcon sx={{ color: getStatusColor(props.section["page"]["status"]) }} />
                  </ListItemIcon>
                  <ListItemText
                    primary={t('domainFinder.details.fields.statusCode')}
                    secondary={
                      props.section["page"]["status"]
                        ? props.section["page"]["status"]
                        : t('domainFinder.details.notAvailable')
                    }
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <StorageIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary={t('domainFinder.details.fields.server')}
                    secondary={
                      props.section["page"]["server"]
                        ? props.section["page"]["server"]
                        : t('domainFinder.details.notAvailable')
                    }
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CategoryIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary={t('domainFinder.details.fields.mimeType')}
                    secondary={
                      props.section["page"]["mimeType"]
                        ? props.section["page"]["mimeType"]
                        : t('domainFinder.details.notAvailable')
                    }
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <BusinessIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary={t('domainFinder.details.fields.asnName')}
                    secondary={
                      props.section["page"]["asnname"]
                        ? props.section["page"]["asnname"]
                        : t('domainFinder.details.notAvailable')
                    }
                  />
                </ListItem>
              </List>
            </Grid>
            <Grid size={6}>
              <List>
                <ListItem>
                  <ListItemIcon>
                    <DomainVerificationIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary={t('domainFinder.details.fields.tlsValidDays')}
                    secondary={
                      props.section["page"]["tlsValidDays"]
                        ? props.section["page"]["tlsValidDays"]
                        : t('domainFinder.details.notAvailable')
                    }
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <DateRangeIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary={t('domainFinder.details.fields.tlsAgeDays')}
                    secondary={
                      props.section["page"]["tlsAgeDays"]
                        ? props.section["page"]["tlsAgeDays"]
                        : t('domainFinder.details.notAvailable')
                    }
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CalendarMonthIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary={t('domainFinder.details.fields.tlsValidFrom')}
                    secondary={
                      props.section["page"]["tlsValidFrom"]
                        ? props.section["page"]["tlsValidFrom"]
                        : t('domainFinder.details.notAvailable')
                    }
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <AdminPanelSettingsIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary={t('domainFinder.details.fields.tlsIssuer')}
                    secondary={
                      props.section["page"]["tlsIssuer"]
                        ? props.section["page"]["tlsIssuer"]
                        : t('domainFinder.details.notAvailable')
                    }
                  />
                </ListItem>
              </List>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <IocLookupDialog open={open} onClose={closeDialog} ioc={ioc} iocType={iocType} />
    </Box>
  );
}

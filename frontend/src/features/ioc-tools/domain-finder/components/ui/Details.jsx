import React from "react";

import IocLookupDialog from '../../../ioc-lookup/shared/components/IocLookupDialog';
import { useIocLookupDialog } from '../../../ioc-lookup/shared/hooks/useIocLookupDialog';
import AdminPanelSettingsIcon from "@mui/icons-material/AdminPanelSettings";
import Box from "@mui/material/Box";
import BusinessIcon from "@mui/icons-material/Business";
import Button from "@mui/material/Button";
import CalendarMonthIcon from "@mui/icons-material/CalendarMonth";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import CategoryIcon from "@mui/icons-material/Category";
import CircleIcon from "@mui/icons-material/Circle";
import DateRangeIcon from "@mui/icons-material/DateRange";
import DomainVerificationIcon from "@mui/icons-material/DomainVerification";
import Grid from "@mui/material/Grid2";
import HttpIcon from "@mui/icons-material/Http";
import LanIcon from "@mui/icons-material/Lan";
import LanguageIcon from "@mui/icons-material/Language";
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import Stack from "@mui/material/Stack";
import StorageIcon from "@mui/icons-material/Storage";
import Typography from "@mui/material/Typography";

function getStatusColor(status) {
  const statusStr = String(status);
  if (statusStr.startsWith('2')) return 'success.main';
  if (statusStr.startsWith('4')) return 'warning.main';
  if (statusStr.startsWith('5')) return 'error.main';
  return 'text.disabled';
}

export default function Details(props) {
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
            Screenshot
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
              No screenshot available
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
                    primary="IP"
                    secondary={
                      props.section["page"]["ip"]
                        ? props.section["page"]["ip"]
                        : "N/A"
                    }
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <LanguageIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary="Country"
                    secondary={
                      props.section["page"]["country"]
                        ? props.section["page"]["country"]
                        : "N/A"
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
                    primary="URL"
                    secondary={
                      props.section["page"]["url"]
                        ? props.section["page"]["url"]
                        : "N/A"
                    }
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <OpenInNewIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary="Result"
                    secondary={
                      props.section["result"] ? props.section["result"] : "N/A"
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
            Analyze IP
          </Button>
          &nbsp;&nbsp;
          <Button
            variant="outlined"
            disableElevation
            size="small"
            onClick={() => openDialog(props.section["task"]["domain"], 'Domain')}
          >
            Analyze Domain
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
                    primary="Status code"
                    secondary={
                      props.section["page"]["status"]
                        ? props.section["page"]["status"]
                        : "N/A"
                    }
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <StorageIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary="Server"
                    secondary={
                      props.section["page"]["server"]
                        ? props.section["page"]["server"]
                        : "N/A"
                    }
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CategoryIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary="MIME type"
                    secondary={
                      props.section["page"]["mimeType"]
                        ? props.section["page"]["mimeType"]
                        : "N/A"
                    }
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <BusinessIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary="ASN Name"
                    secondary={
                      props.section["page"]["asnname"]
                        ? props.section["page"]["asnname"]
                        : "N/A"
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
                    primary="TLS valid days"
                    secondary={
                      props.section["page"]["tlsValidDays"]
                        ? props.section["page"]["tlsValidDays"]
                        : "N/A"
                    }
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <DateRangeIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary="TLS age in days"
                    secondary={
                      props.section["page"]["tlsAgeDays"]
                        ? props.section["page"]["tlsAgeDays"]
                        : "N/A"
                    }
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CalendarMonthIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary="TLS valid from"
                    secondary={
                      props.section["page"]["tlsValidFrom"]
                        ? props.section["page"]["tlsValidFrom"]
                        : "N/A"
                    }
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <AdminPanelSettingsIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary="TLS issuer"
                    secondary={
                      props.section["page"]["tlsIssuer"]
                        ? props.section["page"]["tlsIssuer"]
                        : "N/A"
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

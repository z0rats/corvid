import React from "react";
import { useTranslation } from 'react-i18next';
import Box from "@mui/material/Box";
import BrandingWatermarkIcon from "@mui/icons-material/BrandingWatermark";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import CategoryIcon from "@mui/icons-material/Category";
import FingerprintIcon from "@mui/icons-material/Fingerprint";
import Grid from "@mui/material/Grid";
import HourglassBottomIcon from "@mui/icons-material/HourglassBottom";
import InfoIcon from "@mui/icons-material/Info";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import NumbersIcon from "@mui/icons-material/Numbers";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import PlayCircleFilledWhiteIcon from "@mui/icons-material/PlayCircleFilledWhite";
import ScreenshotMonitorIcon from "@mui/icons-material/ScreenshotMonitor";
import SecurityIcon from "@mui/icons-material/Security";
import StopCircleIcon from "@mui/icons-material/StopCircle";
import Typography from "@mui/material/Typography";
import Link from '@mui/material/Link';
import NoDetails from "../NoDetails";

export default function CheckphishDetails({ result, ioc }) {
  const { t } = useTranslation('iocTools');
  const notAvailable = t('providers.common.notAvailable');

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return notAvailable;
    return new Date(timestamp * 1000).toLocaleString("en-US", {
      dateStyle: "medium",
      timeStyle: "medium",
    });
  };

  if (!result || result.error || result.status !== 'DONE') {
    let message = t('providers.checkphish.unavailable');
    if (result && result.error) {
        message = t('providers.checkphish.errorFetching', { error: result.message || result.error });
    } else if (result && result.status && result.status !== 'DONE') {
        message = t('providers.checkphish.scanStatus', { status: result.status });
    }
    return <NoDetails message={message} />;
  }

  return (
    <Box sx={{ margin: 1, mt:0 }}>
      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: result.screenshot_path ? 7 : 12 }}>
          <Card elevation={0} sx={{ borderRadius: 2, border: '1px solid', borderColor: 'divider' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <InfoIcon color="action" />
                <Typography variant="h6">{t('providers.checkphish.scanDetails')}</Typography>
              </Box>
              <List dense>
                <ListItem>
                  <ListItemIcon sx={{minWidth: 36}}>
                    <NumbersIcon color="action" />
                  </ListItemIcon>
                  <ListItemText primary={t('providers.checkphish.jobId')} secondary={result.job_id || notAvailable} />
                </ListItem>
                <ListItem>
                  <ListItemIcon sx={{minWidth: 36}}>
                    <CategoryIcon color="action" />
                  </ListItemIcon>
                  <ListItemText primary={t('providers.checkphish.scannedUrl')} secondary={result.url || notAvailable} sx={{wordBreak: 'break-all'}}/>
                </ListItem>
                <ListItem>
                  <ListItemIcon sx={{minWidth: 36}}>
                    <FingerprintIcon color="action" />
                  </ListItemIcon>
                  <ListItemText
                    primary={t('providers.checkphish.urlSha256')}
                    secondary={result.url_sha256 || notAvailable}
                    sx={{wordBreak: 'break-all'}}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon sx={{minWidth: 36}}>
                    <HourglassBottomIcon color="action" />
                  </ListItemIcon>
                  <ListItemText primary={t('providers.checkphish.jobStatus')} secondary={result.status || notAvailable} />
                </ListItem>
                <ListItem>
                  <ListItemIcon sx={{minWidth: 36}}>
                    <PlayCircleFilledWhiteIcon color="action" />
                  </ListItemIcon>
                  <ListItemText
                    primary={t('providers.checkphish.scanStart')}
                    secondary={formatTimestamp(result.scan_start_ts)}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon sx={{minWidth: 36}}>
                    <StopCircleIcon color="action" />
                  </ListItemIcon>
                  <ListItemText
                    primary={t('providers.checkphish.scanEnd')}
                    secondary={formatTimestamp(result.scan_end_ts)}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon sx={{minWidth: 36}}>
                    <SecurityIcon color="action" />
                  </ListItemIcon>
                  <ListItemText
                    primary={t('providers.checkphish.disposition')}
                    secondary={result.disposition || notAvailable}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon sx={{minWidth: 36}}>
                    <BrandingWatermarkIcon color="action" />
                  </ListItemIcon>
                  <ListItemText primary={t('providers.checkphish.detectedBrand')} secondary={result.brand || notAvailable} />
                </ListItem>
                {result.insights && (
                    <ListItem>
                        <ListItemIcon sx={{minWidth: 36}}>
                            <OpenInNewIcon color="action" />
                        </ListItemIcon>
                        <ListItemText
                            primary={t('providers.checkphish.insights')}
                            secondary={result.insights}
                        />
                    </ListItem>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {result.screenshot_path && (
          <Grid size={{ xs: 12, md: 5 }}>
            <Card elevation={0} sx={{ borderRadius: 2, border: '1px solid', borderColor: 'divider' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <ScreenshotMonitorIcon color="action" />
                  <Typography variant="h6">{t('providers.checkphish.screenshot')}</Typography>
                </Box>
                <Link
                  href={result.screenshot_path}
                  target="_blank"
                  rel="noopener noreferrer"
                  sx={{ display: 'block', mt: 1 }}
                >
                  <Box
                    component="img"
                    src={result.screenshot_path}
                    alt={t('providers.checkphish.screenshotAlt')}
                    sx={{
                      maxWidth: "100%",
                      height: "auto",
                      borderRadius: 1,
                      border: '1px solid',
                      borderColor: 'divider'
                    }}
                  />
                </Link>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );
}

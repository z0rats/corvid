import React, { useState } from "react";
import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router';
import ReactCountryFlag from "react-country-flag";
import { useDnsDumpster } from "../../hooks/api/useDnsDumpster";

import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Collapse from '@mui/material/Collapse';
import IconButton from '@mui/material/IconButton';
import LinearProgress from '@mui/material/LinearProgress';
import Link from '@mui/material/Link';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';

import DnsOutlinedIcon from "@mui/icons-material/DnsOutlined";
import HttpIcon from "@mui/icons-material/Http";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDownOutlined";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUpOutlined";
import LanguageIcon from "@mui/icons-material/Language";
import MailOutlineIcon from "@mui/icons-material/MailOutlineOutlined";
import VpnKeyOutlinedIcon from "@mui/icons-material/VpnKeyOutlined";

const RECORD_GROUPS = [
  { key: 'a', icon: DnsOutlinedIcon },
  { key: 'ns', icon: LanguageIcon },
  { key: 'mx', icon: MailOutlineIcon },
  { key: 'cname', icon: DnsOutlinedIcon },
];

function BannerChips({ banner }) {
  if (!banner) return null;
  return (
    <Stack direction="row" spacing={0.5} sx={{ gap: 0.5, flexWrap: 'wrap' }}>
      {banner.server && <Chip size="small" variant="outlined" label={banner.server} />}
      {banner.title && <Chip size="small" variant="outlined" label={banner.title} />}
      {banner.cn && <Chip size="small" variant="outlined" label={`CN: ${banner.cn}`} />}
      {(banner.apps || []).map((app) => (
        <Chip key={app} size="small" color="primary" variant="outlined" label={app} />
      ))}
    </Stack>
  );
}

function IpRow({ ip, t }) {
  const [open, setOpen] = useState(false);
  const hasBanners = Boolean(ip.banner_http || ip.banner_https);

  return (
    <Box sx={{ borderRadius: 1, bgcolor: 'action.hover', p: 1 }}>
      <Stack direction="row" spacing={1} sx={{ gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
        {ip.country_code && (
          <ReactCountryFlag countryCode={ip.country_code} title={ip.country || ip.country_code} />
        )}
        <Chip size="small" variant="filled" label={ip.ip} />
        {ip.asn && (
          <Chip
            size="small"
            variant="outlined"
            icon={<VpnKeyOutlinedIcon fontSize="small" />}
            label={`AS${ip.asn.replace(/^AS/i, '')}${ip.asn_name ? ` · ${ip.asn_name}` : ''}`}
          />
        )}
        {ip.ptr && (
          <Typography variant="caption" color="text.secondary">
            {t('domainFinder.dnsDumpster.ptr')}: {ip.ptr}
          </Typography>
        )}
        {hasBanners && (
          <IconButton size="small" onClick={() => setOpen(!open)} aria-label={t('domainFinder.dnsDumpster.toggleBanner')}>
            <HttpIcon fontSize="small" color={open ? 'primary' : 'action'} />
            {open ? <KeyboardArrowUpIcon fontSize="small" /> : <KeyboardArrowDownIcon fontSize="small" />}
          </IconButton>
        )}
      </Stack>

      {hasBanners && (
        <Collapse in={open} timeout="auto" unmountOnExit>
          <Stack spacing={1} sx={{ mt: 1, pl: 1 }}>
            {ip.banner_http && (
              <Box>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                  {t('domainFinder.dnsDumpster.httpBanner')}
                </Typography>
                <BannerChips banner={ip.banner_http} />
              </Box>
            )}
            {ip.banner_https && (
              <Box>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                  {t('domainFinder.dnsDumpster.httpsBanner')}
                </Typography>
                <BannerChips banner={ip.banner_https} />
              </Box>
            )}
          </Stack>
        </Collapse>
      )}
    </Box>
  );
}

function HostGroup({ groupKey, icon: Icon, hosts, t }) {
  if (!hosts || hosts.length === 0) return null;

  return (
    <Box>
      <Stack
        direction="row"
        spacing={1}
        sx={{
          alignItems: "center",
          mb: 1
        }}>
        <Icon fontSize="small" color="action" />
        <Typography variant="subtitle2">
          {t(`domainFinder.dnsDumpster.groups.${groupKey}`, { count: hosts.length })}
        </Typography>
      </Stack>
      <Stack spacing={1.5}>
        {hosts.map((host) => (
          <Box key={host.host}>
            <Typography variant="body2" sx={{ fontWeight: 500, mb: 0.5, wordBreak: 'break-all' }}>
              {host.host}
            </Typography>
            {host.ips.length > 0 && (
              <Stack spacing={0.75}>
                {host.ips.map((ip) => (
                  <IpRow key={`${host.host}_${ip.ip}`} ip={ip} t={t} />
                ))}
              </Stack>
            )}
          </Box>
        ))}
      </Stack>
    </Box>
  );
}

export default function DnsDumpsterPanel({ domain }) {
  const { t } = useTranslation('iocTools');
  const theme = useTheme();
  const { data, loading, error, notConfigured, unsupported } = useDnsDumpster(domain);

  if (unsupported) return null;

  if (loading) {
    return (
      <>
        <LinearProgress />
        <br />
      </>
    );
  }

  if (notConfigured) {
    return (
      <Alert
        severity="info"
        variant="outlined"
        sx={{ borderRadius: 1, mb: 2 }}
        action={
          <Link component={RouterLink} to="/settings/apikeys" underline="hover" sx={{ whiteSpace: 'nowrap', alignSelf: 'center' }}>
            {t('domainFinder.dnsDumpster.addKeyAction')}
          </Link>
        }
      >
        {t('domainFinder.dnsDumpster.notConfigured')}
      </Alert>
    );
  }

  if (error) {
    return (
      <Alert severity="warning" variant="outlined" sx={{ borderRadius: 1, mb: 2 }}>
        {t('domainFinder.dnsDumpster.errorPrefix')} {error}
      </Alert>
    );
  }

  if (!data) return null;

  const hasAnyRecords = RECORD_GROUPS.some((group) => data[group.key]?.length > 0) || data.txt.length > 0;

  return (
    <Card sx={{ mb: 2, p: 1, borderRadius: 1, boxShadow: 0 }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 1.5 }}>
          {t('domainFinder.dnsDumpster.title')}
        </Typography>

        {!hasAnyRecords ? (
          <Typography variant="body2" color="text.secondary">
            {t('domainFinder.dnsDumpster.noRecords')}
          </Typography>
        ) : (
          <Stack spacing={2.5}>
            {RECORD_GROUPS.map((group) => (
              <HostGroup key={group.key} groupKey={group.key} icon={group.icon} hosts={data[group.key]} t={t} />
            ))}

            {data.txt.length > 0 && (
              <Box>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>
                  {t('domainFinder.dnsDumpster.groups.txt', { count: data.txt.length })}
                </Typography>
                <Stack spacing={0.5}>
                  {data.txt.map((record, index) => (
                    <Typography
                      key={`txt_${index}`}
                      variant="body2"
                      sx={{ fontFamily: 'monospace', bgcolor: theme.palette.action.hover, borderRadius: 1, p: 0.75, wordBreak: 'break-all' }}
                    >
                      {record}
                    </Typography>
                  ))}
                </Stack>
              </Box>
            )}
          </Stack>
        )}

        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
          {t('domainFinder.dnsDumpster.freeTierCaption', { count: data.total_a_records })}
        </Typography>
      </CardContent>
    </Card>
  );
}

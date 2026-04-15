import BugReportIcon from '@mui/icons-material/BugReport';
import EmailIcon from '@mui/icons-material/Email';
import FingerprintIcon from '@mui/icons-material/Fingerprint';
import LanIcon from '@mui/icons-material/Lan';
import LinkIcon from '@mui/icons-material/Link';
import PublicIcon from '@mui/icons-material/Public';
import React from "react";

export const TLP_COLORS = {
  "TLP:RED": "#FF0000",
  "TLP:AMBER": "#FFBF00",
  "TLP:GREEN": "#00FF00",
  "TLP:CLEAR": "#CCCCCC",
};

export const TLP_OPTIONS = [
  { value: "", label: "All" },
  { value: "TLP:CLEAR", label: "TLP:CLEAR" },
  { value: "TLP:GREEN", label: "TLP:GREEN" },
  { value: "TLP:AMBER", label: "TLP:AMBER" },
  { value: "TLP:RED", label: "TLP:RED" },
];

export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 15,
  DEFAULT_PAGE: 1,
};

export const SETTINGS = {
  MIN_FETCH_INTERVAL: 5,
  MAX_FETCH_INTERVAL: 720,
  MIN_RETENTION_DAYS: 0,
  MAX_WIDTH: 400,
};

export const RETENTION_OPTIONS = [
  { value: 0, label: "Unlimited" },
  { value: 7, label: "7 days" },
  { value: 14, label: "14 days" },
  { value: 30, label: "30 days" },
  { value: 60, label: "60 days" },
  { value: 90, label: "90 days" },
  { value: 180, label: "180 days" },
  { value: 365, label: "1 year" },
];

export const FETCH_INTERVAL_OPTIONS = [
  { value: 5, label: "5 minutes" },
  { value: 15, label: "15 minutes" },
  { value: 30, label: "30 minutes" },
  { value: 60, label: "1 hour" },
  { value: 120, label: "2 hours" },
  { value: 240, label: "4 hours" },
  { value: 480, label: "8 hours" },
  { value: 720, label: "12 hours" },
];

export const DEFAULT_FILTERS = {
  start_date: "",
  end_date: "",
  has_matches: null,
  has_iocs: null,
  has_relevant_iocs: null,
  has_analysis: null,
  has_note: null,
  tlp: "",
  read: null,
};

export const TIME_RANGE_OPTIONS = [
  { value: '8h', label: 'Last 8 Hours' },
  { value: '24h', label: 'Last 24 Hours' },
  { value: '2d', label: 'Last 2 Days' },
  { value: '7d', label: 'Last 7 Days' },
  { value: '14d', label: 'Last 14 Days' },
  { value: '30d', label: 'Last 30 Days' },
  { value: 'alltime', label: 'All Time' },
];

export const DEFAULT_CONFIG = {
  retention_days: 0,
  background_fetch_enabled: false,
  fetch_interval_minutes: 5,
};

export const IOC_TYPES = [
  { type: "ips", label: "IP Addresses", icon: <LanIcon color="primary" /> },
  { type: "md5", label: "MD5 Hashes", icon: <FingerprintIcon color="secondary" /> },
  { type: "sha1", label: "SHA1 Hashes", icon: <FingerprintIcon color="secondary" /> },
  { type: "sha256", label: "SHA256 Hashes", icon: <FingerprintIcon color="secondary" /> },
  { type: "urls", label: "URLs", icon: <LinkIcon color="success" /> },
  { type: "domains", label: "Domains", icon: <PublicIcon color="info" /> },
  { type: "emails", label: "Emails", icon: <EmailIcon color="warning" /> },
  { type: "cves", label: "CVEs", icon: <BugReportIcon color="error" /> },
];

export const IOC_TYPE_SELECT_OPTIONS = [
  { value: 'ips', label: 'IP Addresses' },
  { value: 'domains', label: 'Domains' },
  { value: 'urls', label: 'URLs' },
  { value: 'md5_hashes', label: 'MD5 Hashes' },
  { value: 'sha1_hashes', label: 'SHA1 Hashes' },
  { value: 'sha256_hashes', label: 'SHA256 Hashes' },
  { value: 'emails', label: 'Emails' },
];

export const RISK_CHIP_COLORS = {
  High: 'error',
  Medium: 'warning',
  Low: 'success',
  Informational: 'info',
};

export const CTI_OPTIONS = {
  industries: ["Finance", "Healthcare", "Technology", "Retail", "Energy"],
  companySizes: ["Small", "Medium", "Large"],
  geographicalScopes: ["North America", "EMEA", "APAC", "Global"],
  languages: ["English", "Spanish", "French", "German", "Chinese"],
  attackTypes: ["Ransomware", "DDoS", "Phishing", "Insider Threats", "Supply Chain"],
  priorities: ["High", "Medium", "Low"],
  motivations: ["Financial", "Political", "Data Theft", "Reputational Damage"],
};

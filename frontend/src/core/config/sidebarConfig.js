import NewspaperIcon from "@mui/icons-material/Newspaper";
import SearchIcon from "@mui/icons-material/Search";
import MailIcon from "@mui/icons-material/Mail";
import DocumentScannerIcon from "@mui/icons-material/DocumentScanner";
import TravelExploreIcon from "@mui/icons-material/TravelExplore";
import PsychologyIcon from "@mui/icons-material/Psychology";
import CalculateIcon from "@mui/icons-material/Calculate";
import RuleIcon from "@mui/icons-material/Rule";
import InfoIcon from "@mui/icons-material/Info";
import ViewModuleIcon from "@mui/icons-material/ViewModule";
import KeyIcon from "@mui/icons-material/Key";
import PsychologyAltIcon from "@mui/icons-material/PsychologyAlt";
import SettingsIcon from "@mui/icons-material/Settings";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import ArticleIcon from "@mui/icons-material/Article";
import RssFeedIcon from "@mui/icons-material/RssFeed";
import ManageSearchIcon from "@mui/icons-material/ManageSearch";
import FindInPageIcon from "@mui/icons-material/FindInPage";
import ViewHeadlineIcon from "@mui/icons-material/ViewHeadline";
import CreateIcon from "@mui/icons-material/Create";
import ViewListIcon from "@mui/icons-material/ViewList";
import HealthAndSafetyIcon from "@mui/icons-material/HealthAndSafety";
import NetworkCheckIcon from "@mui/icons-material/NetworkCheck";

export const mainMenuItems = [
  {
    name: "Newsfeed",
    icon: <NewspaperIcon />,
    path: "/newsfeed",
    moduleId: "newsfeed",
  },
  {
    name: "IOC Tools",
    icon: <SearchIcon />,
    path: "/ioc-tools",
    moduleId: "ioc_tools",
  },
  {
    name: "Email Analyzer",
    icon: <MailIcon />,
    path: "/email-analyzer",
    moduleId: "email_analyzer",
  },
  {
    name: "AI Templates",
    icon: <PsychologyIcon />,
    path: "/ai-templates",
    moduleId: "llm_templates",
  },
  {
    name: "CVSS Calculator",
    icon: <CalculateIcon />,
    path: "/cvss-calculator",
    moduleId: "cvss_calculator",
  },
  {
    name: "Detection Rules",
    icon: <RuleIcon />,
    path: "/rules",
    moduleId: "rule_creator",
  },
];

export const aiTemplatesTabs = [
  {
    label: "Templates",
    path: "/ai-templates/templates",
    icon: <ViewListIcon />,
  },
  {
    label: "Create Template",
    path: "/ai-templates/create-template",
    icon: <CreateIcon />,
  },
];

export const iocToolsTabs = [
  {
    label: "Single Lookup",
    path: "/ioc-tools/lookup",
    icon: <SearchIcon />,
  },
  {
    label: "Bulk Lookup",
    path: "/ioc-tools/bulk",
    icon: <ManageSearchIcon />,
  },
  {
    label: "Domain Finder",
    path: "/ioc-tools/domain-finder",
    icon: <TravelExploreIcon />,
  },
  {
    label: "Extractor",
    path: "/ioc-tools/extractor",
    icon: <DocumentScannerIcon />,
  },
  {
    label: "Defang/Fang",
    path: "/ioc-tools/defanger",
    icon: <HealthAndSafetyIcon />,
  },
];

export const newsfeedTabs = [
  {
    label: "Feed",
    path: "/newsfeed/feed",
    icon: <RssFeedIcon />,
  },
  {
    label: "Trends",
    path: "/newsfeed/trends",
    icon: <TrendingUpIcon />,
  },
  {
    label: "Headline View",
    path: "/newsfeed/headlines",
    icon: <ViewHeadlineIcon />,
  },
  {
    label: "News Report",
    path: "/newsfeed/report",
    icon: <ArticleIcon />,
  },
  {
    label: "Settings",
    path: "/newsfeed/settings",
    icon: <SettingsIcon />,
    children: [
      {
        label: "General",
        path: "/newsfeed/settings",
        icon: <SettingsIcon />,
      },
      {
        label: "Manage Feeds",
        path: "/newsfeed/settings/feeds",
        icon: <SettingsIcon />,
      },
      {
        label: "Keyword Matching",
        path: "/newsfeed/settings/keywords",
        icon: <SettingsIcon />,
      },
      {
        label: "CTI Settings",
        path: "/newsfeed/settings/cti",
        icon: <SettingsIcon />,
      },
      {
        label: "Trends",
        path: "/newsfeed/settings/trends",
        icon: <SettingsIcon />,
      },
    ],
  },
];

export const settingsTabs = [
  { label: "API Keys", path: "/settings/apikeys", icon: <KeyIcon /> },
  { label: "AI Settings", path: "/settings/ai-settings", icon: <PsychologyAltIcon /> },
  { label: "Modules", path: "/settings/modules", icon: <ViewModuleIcon /> },
  { label: "About", path: "/settings/about", icon: <InfoIcon /> },
];

export const cvssTabs = [
  { label: "CVSS 3.1", path: "/cvss-calculator/cvss-3.1", icon: <CalculateIcon /> },
  { label: "CVSS 4.0", path: "/cvss-calculator/cvss-4.0", icon: <CalculateIcon /> },
];

export const rulesTabs = [
  { label: "Sigma", path: "/rules/sigma", icon: <ManageSearchIcon /> },
  { label: "Yara", path: "/rules/yara", icon: <FindInPageIcon /> },
  { label: "Snort", path: "/rules/snort", icon: <NetworkCheckIcon /> },
];

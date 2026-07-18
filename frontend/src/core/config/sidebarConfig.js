import NewspaperIcon from "@mui/icons-material/Newspaper";
import SearchIcon from "@mui/icons-material/Search";
import MailIcon from "@mui/icons-material/Mail";
import ImageIcon from "@mui/icons-material/Image";
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
import PersonSearchIcon from "@mui/icons-material/PersonSearch";
import HistoryIcon from "@mui/icons-material/History";
import MarkEmailReadIcon from "@mui/icons-material/MarkEmailRead";
import RedditIcon from "@mui/icons-material/Reddit";
import TroubleshootIcon from "@mui/icons-material/Troubleshoot";
import GitHubIcon from "@mui/icons-material/GitHub";

const MAIN_MENU_ITEMS_CONFIG = [
  {
    i18nKey: "nav.newsfeed",
    icon: <NewspaperIcon />,
    path: "/newsfeed",
    moduleId: "newsfeed",
  },
  {
    i18nKey: "nav.iocTools",
    icon: <SearchIcon />,
    path: "/ioc-tools",
    moduleId: "ioc_tools",
  },
  {
    i18nKey: "nav.emailAnalyzer",
    icon: <MailIcon />,
    path: "/email-analyzer",
    moduleId: "email_analyzer",
  },
  {
    i18nKey: "nav.imageTools",
    icon: <ImageIcon />,
    path: "/image-tools",
    moduleId: "image_tools",
  },
  {
    i18nKey: "nav.aiTemplates",
    icon: <PsychologyIcon />,
    path: "/ai-templates",
    moduleId: "llm_templates",
  },
  {
    i18nKey: "nav.cvssCalculator",
    icon: <CalculateIcon />,
    path: "/cvss-calculator",
    moduleId: "cvss_calculator",
  },
  {
    i18nKey: "nav.detectionRules",
    icon: <RuleIcon />,
    path: "/rules",
    moduleId: "rule_creator",
  },
  {
    i18nKey: "nav.usernameSearch",
    icon: <PersonSearchIcon />,
    path: "/username-search",
    moduleId: "username_search",
  },
  {
    i18nKey: "nav.emailSearch",
    icon: <MarkEmailReadIcon />,
    path: "/email-search",
    moduleId: "email_search",
  },
  {
    i18nKey: "nav.redditSearch",
    icon: <RedditIcon />,
    path: "/reddit-search",
    moduleId: "reddit_search",
  },
  {
    i18nKey: "nav.dorkRunner",
    icon: <TroubleshootIcon />,
    path: "/dork-runner",
    moduleId: "dork_runner",
  },
  {
    i18nKey: "nav.gitRecon",
    icon: <GitHubIcon />,
    path: "/git-recon",
    moduleId: "git_recon",
  },
];

const AI_TEMPLATES_TABS_CONFIG = [
  {
    i18nKey: "nav.aiTemplatesTabs.templates",
    path: "/ai-templates/templates",
    icon: <ViewListIcon />,
  },
  {
    i18nKey: "nav.aiTemplatesTabs.createTemplate",
    path: "/ai-templates/create-template",
    icon: <CreateIcon />,
  },
];

const IOC_TOOLS_TABS_CONFIG = [
  {
    i18nKey: "nav.iocToolsTabs.singleLookup",
    path: "/ioc-tools/lookup",
    icon: <SearchIcon />,
  },
  {
    i18nKey: "nav.iocToolsTabs.lookupHistory",
    path: "/ioc-tools/lookup/history",
    icon: <HistoryIcon />,
  },
  {
    i18nKey: "nav.iocToolsTabs.bulkLookup",
    path: "/ioc-tools/bulk",
    icon: <ManageSearchIcon />,
  },
  {
    i18nKey: "nav.iocToolsTabs.domainFinder",
    path: "/ioc-tools/domain-finder",
    icon: <TravelExploreIcon />,
  },
  {
    i18nKey: "nav.iocToolsTabs.extractor",
    path: "/ioc-tools/extractor",
    icon: <DocumentScannerIcon />,
  },
  {
    i18nKey: "nav.iocToolsTabs.defangFang",
    path: "/ioc-tools/defanger",
    icon: <HealthAndSafetyIcon />,
  },
];

const NEWSFEED_TABS_CONFIG = [
  {
    i18nKey: "nav.newsfeedTabs.feed",
    path: "/newsfeed/feed",
    icon: <RssFeedIcon />,
  },
  {
    i18nKey: "nav.newsfeedTabs.trends",
    path: "/newsfeed/trends",
    icon: <TrendingUpIcon />,
  },
  {
    i18nKey: "nav.newsfeedTabs.headlineView",
    path: "/newsfeed/headlines",
    icon: <ViewHeadlineIcon />,
  },
  {
    i18nKey: "nav.newsfeedTabs.newsReport",
    path: "/newsfeed/report",
    icon: <ArticleIcon />,
  },
  {
    i18nKey: "nav.newsfeedTabs.settings",
    path: "/newsfeed/settings",
    icon: <SettingsIcon />,
    children: [
      {
        i18nKey: "nav.newsfeedTabs.settingsGeneral",
        path: "/newsfeed/settings",
        icon: <SettingsIcon />,
      },
      {
        i18nKey: "nav.newsfeedTabs.manageFeeds",
        path: "/newsfeed/settings/feeds",
        icon: <SettingsIcon />,
      },
      {
        i18nKey: "nav.newsfeedTabs.keywordMatching",
        path: "/newsfeed/settings/keywords",
        icon: <SettingsIcon />,
      },
      {
        i18nKey: "nav.newsfeedTabs.ctiSettings",
        path: "/newsfeed/settings/cti",
        icon: <SettingsIcon />,
      },
      {
        i18nKey: "nav.newsfeedTabs.trends",
        path: "/newsfeed/settings/trends",
        icon: <SettingsIcon />,
      },
    ],
  },
];

const SETTINGS_TABS_CONFIG = [
  { i18nKey: "nav.settingsTabs.apiKeys", path: "/settings/apikeys", icon: <KeyIcon /> },
  { i18nKey: "nav.settingsTabs.aiSettings", path: "/settings/ai-settings", icon: <PsychologyAltIcon /> },
  { i18nKey: "nav.settingsTabs.modules", path: "/settings/modules", icon: <ViewModuleIcon /> },
  { i18nKey: "nav.settingsTabs.about", path: "/settings/about", icon: <InfoIcon /> },
];

const CVSS_TABS_CONFIG = [
  { i18nKey: "nav.cvssTabs.cvss31", path: "/cvss-calculator/cvss-3.1", icon: <CalculateIcon /> },
  { i18nKey: "nav.cvssTabs.cvss40", path: "/cvss-calculator/cvss-4.0", icon: <CalculateIcon /> },
];

const RULES_TABS_CONFIG = [
  { i18nKey: "nav.rulesTabs.sigma", path: "/rules/sigma", icon: <ManageSearchIcon /> },
  { i18nKey: "nav.rulesTabs.yara", path: "/rules/yara", icon: <FindInPageIcon /> },
  { i18nKey: "nav.rulesTabs.snort", path: "/rules/snort", icon: <NetworkCheckIcon /> },
];

const USERNAME_SEARCH_TABS_CONFIG = [
  { i18nKey: "nav.usernameSearchTabs.newSearch", path: "/username-search/new", icon: <PersonSearchIcon /> },
  { i18nKey: "nav.usernameSearchTabs.history", path: "/username-search/history", icon: <HistoryIcon /> },
  { i18nKey: "nav.usernameSearchTabs.settings", path: "/username-search/settings", icon: <SettingsIcon /> },
];

const EMAIL_SEARCH_TABS_CONFIG = [
  { i18nKey: "nav.emailSearchTabs.newSearch", path: "/email-search/new", icon: <MarkEmailReadIcon /> },
  { i18nKey: "nav.emailSearchTabs.history", path: "/email-search/history", icon: <HistoryIcon /> },
  { i18nKey: "nav.emailSearchTabs.settings", path: "/email-search/settings", icon: <SettingsIcon /> },
];

const REDDIT_SEARCH_TABS_CONFIG = [
  { i18nKey: "nav.redditSearchTabs.newSearch", path: "/reddit-search/new", icon: <RedditIcon /> },
  { i18nKey: "nav.redditSearchTabs.history", path: "/reddit-search/history", icon: <HistoryIcon /> },
];

const GIT_RECON_TABS_CONFIG = [
  { i18nKey: "nav.gitReconTabs.newSearch", path: "/git-recon/new", icon: <GitHubIcon /> },
  { i18nKey: "nav.gitReconTabs.history", path: "/git-recon/history", icon: <HistoryIcon /> },
];

const translateItem = (t, { i18nKey, children, ...rest }) => ({
  ...rest,
  label: t(i18nKey),
  name: t(i18nKey),
  ...(children ? { children: children.map(child => translateItem(t, child)) } : {}),
});

export const getMainMenuItems = (t) => MAIN_MENU_ITEMS_CONFIG.map(item => translateItem(t, item));
export const getAiTemplatesTabs = (t) => AI_TEMPLATES_TABS_CONFIG.map(item => translateItem(t, item));
export const getIocToolsTabs = (t) => IOC_TOOLS_TABS_CONFIG.map(item => translateItem(t, item));
export const getNewsfeedTabs = (t) => NEWSFEED_TABS_CONFIG.map(item => translateItem(t, item));
export const getSettingsTabs = (t) => SETTINGS_TABS_CONFIG.map(item => translateItem(t, item));
export const getCvssTabs = (t) => CVSS_TABS_CONFIG.map(item => translateItem(t, item));
export const getRulesTabs = (t) => RULES_TABS_CONFIG.map(item => translateItem(t, item));
export const getUsernameSearchTabs = (t) => USERNAME_SEARCH_TABS_CONFIG.map(item => translateItem(t, item));
export const getEmailSearchTabs = (t) => EMAIL_SEARCH_TABS_CONFIG.map(item => translateItem(t, item));
export const getRedditSearchTabs = (t) => REDDIT_SEARCH_TABS_CONFIG.map(item => translateItem(t, item));
export const getGitReconTabs = (t) => GIT_RECON_TABS_CONFIG.map(item => translateItem(t, item));

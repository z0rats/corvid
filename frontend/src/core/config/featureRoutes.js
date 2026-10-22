import { lazy } from 'react';

const CvssCalculator = lazy(() => import("../../features/cvss-calculator/CvssCalculator"));
const EmailAnalyzer = lazy(() => import("../../features/email-analyzer/EmailAnalyzer"));
const ImageTools = lazy(() => import("../../features/image-tools/ImageTools"));
const IocTools = lazy(() => import("../../features/ioc-tools/IocTools"));
const Newsfeed = lazy(() => import("../../features/newsfeed/Newsfeed"));
const Settings = lazy(() => import("../../features/settings/Settings"));
const RuleCreator = lazy(() => import("../../features/rule-creator/RuleCreator"));
const AiTemplates = lazy(() => import("../../features/llm-templates/AiTemplates"));
const UsernameSearch = lazy(() => import("../../features/username-search/UsernameSearch"));
const EmailSearch = lazy(() => import("../../features/email-search/EmailSearch"));
const RedditSearch = lazy(() => import("../../features/reddit-search/RedditSearch"));
const DorkRunner = lazy(() => import("../../features/dork-runner/DorkRunner"));
const GitRecon = lazy(() => import("../../features/git-recon/GitRecon"));
const Amass = lazy(() => import("../../features/amass/Amass"));
const RuBusinessCheck = lazy(() => import("../../features/ru-business-check/RuBusinessCheck"));
const YoutubeLookup = lazy(() => import("../../features/youtube/YoutubeLookup"));
const SteamRecon = lazy(() => import("../../features/steam-recon/SteamRecon"));
const InstagramSearch = lazy(() => import("../../features/instagram-search/InstagramSearch"));
const TelegramSearch = lazy(() => import("../../features/telegram-search/TelegramSearch"));
const PhoneSearch = lazy(() => import("../../features/phone-search/PhoneSearch"));
const SanctionsSearch = lazy(() => import("../../features/sanctions-search/SanctionsSearch"));
const Investigations = lazy(() => import("../../features/investigations/Investigations"));

/** Every lazy feature page, mounted under the layout at `path`. */
export const FEATURE_ROUTES = [
  { path: 'newsfeed/*', Component: Newsfeed },
  { path: 'settings/*', Component: Settings },
  { path: 'ai-templates/*', Component: AiTemplates },
  { path: 'ioc-tools/*', Component: IocTools },
  { path: 'email-analyzer/*', Component: EmailAnalyzer },
  { path: 'image-tools/*', Component: ImageTools },
  { path: 'cvss-calculator/*', Component: CvssCalculator },
  { path: 'rules/*', Component: RuleCreator },
  { path: 'username-search/*', Component: UsernameSearch },
  { path: 'email-search/*', Component: EmailSearch },
  { path: 'reddit-search/*', Component: RedditSearch },
  { path: 'dork-runner/*', Component: DorkRunner },
  { path: 'git-recon/*', Component: GitRecon },
  { path: 'amass/*', Component: Amass },
  { path: 'ru-business-check/*', Component: RuBusinessCheck },
  { path: 'youtube/*', Component: YoutubeLookup },
  { path: 'steam-recon/*', Component: SteamRecon },
  { path: 'instagram-search/*', Component: InstagramSearch },
  { path: 'telegram-search/*', Component: TelegramSearch },
  { path: 'phone-search/*', Component: PhoneSearch },
  { path: 'sanctions-search/*', Component: SanctionsSearch },
  { path: 'investigations/*', Component: Investigations },
];

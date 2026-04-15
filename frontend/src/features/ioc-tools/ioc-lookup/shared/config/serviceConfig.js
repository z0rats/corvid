import AbuseIpdbDetails from '../components/service-details/AbuseIPDB/AbuseIpdbDetails';
import AlienvaultDetails from '../components/service-details/Alienvault/AlienvaultDetails';
import CheckphishDetails from '../components/service-details/Checkphish/CheckphishDetails';
import CrowdSecDetailsComponent from '../components/service-details/CrowdSec/CrowdSecDetails';
import CrowdStrikeDetailsComponent from '../components/service-details/CrowdStrike/CrowdStrike';
import EmailrepioDetails from '../components/service-details/EmailrepIO/EmailrepioDetails';
import GithubDetails from '../components/service-details/GitHub/GithubDetails';
import HaveibeenpwndDetails from '../components/service-details/HIBP/HaveibeenpwndDetails';
import HunterioDetails from '../components/service-details/HunterIO/HunterioDetails';
import IpQualityscoreDetails from '../components/service-details/IpQualityScore/IpqualityscoreDetails';
import MandiantDetails from '../components/service-details/Mandiant/MandiantDetails';
import MaltiverseDetails from '../components/service-details/Maltiverse/MaltiverseDetails';
import MalwarebazaarDetails from '../components/service-details/Malwarebazaar/MalwarebazaarDetails';
import NistNvdDetailsComponent from '../components/service-details/NistNVD/NistNvdDetails';
import PulsediveDetails from '../components/service-details/Pulsedive/PulsediveDetails';
import RedditDetails from '../components/service-details/Reddit/RedditDetails';
import SafeBrowseDetails from '../components/service-details/GoogleSafeBrowsing/SafebrowsingDetails';
import ShodanDetailsComponent from '../components/service-details/Shodan/ShodanDetails';
import ThreatfoxDetails from '../components/service-details/ThreatFox/ThreatfoxDetails';
import TwitterDetails from '../components/service-details/Twitter/TwitterDetails';
import VirustotalDetailsComponent from '../components/service-details/Virustotal/VirustotalDetails';
import UrlHausDetails from '../components/service-details/UrlHaus/UrlHausDetails';
import UrlScanDetails from '../components/service-details/UrlScan/UrlScanDetails';
import { withErrorHandling, withNoDataCheck, scoreTlpMapper } from '../utils/serviceConfigHelpers';


/**
 * Simple endpoint generator for the unified backend API.
 * @param {string} serviceKey
 * @returns {function}
 */
const createSingleEndpoint = (serviceKey) => (ioc, iocType) =>
  `/api/ioc/lookup/${serviceKey}?ioc=${encodeURIComponent(ioc)}&ioc_type=${encodeURIComponent(iocType)}`;

/**
 * Unified service definitions.
 * - name: Display name for the UI.
 * - icon: Filename for the service's icon.
 * - detailComponent: The React component used to render detailed results.
 * - requiredKeys: Array of API key names needed from global state.
 * - supportedIocTypes: Array of IOC types the service supports.
 * - lookupEndpoint: Function to generate the API request URL.
 * - getSummaryAndTlp: Function to process the API response into a display summary and TLP color.
 */
export const SERVICE_DEFINITIONS = {
  abuseipdb: {
    name: 'AbuseIPDB',
    icon: 'aipdb_logo_small',
    detailComponent: AbuseIpdbDetails,
    requiredKeys: ['abuseipdb'],
    supportedIocTypes: ['IPv4'],
    lookupEndpoint: createSingleEndpoint('abuseipdb'),
    getSummaryAndTlp: withErrorHandling(withNoDataCheck((responseData) => {
      const { abuseConfidenceScore } = responseData.data;
      const tlp = scoreTlpMapper(abuseConfidenceScore);
      return { summary: `Abuse Score: ${abuseConfidenceScore}%`, tlp, keyMetric: `${abuseConfidenceScore}%` };
    }, 'data')),
  },
  alienvault: {
    name: 'AlienVault OTX',
    icon: 'avotx_logo_small',
    detailComponent: AlienvaultDetails,
    requiredKeys: ['alienvault'],
    supportedIocTypes: ['IPv4', 'IPv6', 'Domain', 'URL', 'MD5', 'SHA1', 'SHA256'],
    lookupEndpoint: createSingleEndpoint('alienvault'),
    getSummaryAndTlp: withErrorHandling(withNoDataCheck((responseData) => {
        const pulseCount = responseData.pulse_info?.count || 0;
        const hasMalware = responseData.section_malware?.data?.length > 0;
        const reputationData = responseData.section_reputation?.reputation;
        const hasMaliciousActivity = reputationData?.activities?.some(
            act => act.name?.toLowerCase().includes('malicious')
        );

        let tlp = 'GREEN';
        if (hasMaliciousActivity || hasMalware) tlp = 'RED';
        else if (pulseCount > 0) tlp = 'AMBER';

        const parts = [`${pulseCount} pulse(s)`];
        if (hasMalware) parts.push(`${responseData.section_malware.data.length} malware sample(s)`);

        return { summary: parts.join(', '), tlp, keyMetric: pulseCount };
    })),
  },
  checkphish: {
    name: 'CheckPhish',
    icon: 'checkphish_logo_small',
    detailComponent: CheckphishDetails,
    requiredKeys: ['checkphishai'],
    supportedIocTypes: ['IPv4', 'Domain', 'URL'],
    lookupEndpoint: createSingleEndpoint('checkphish'),
    getSummaryAndTlp: withErrorHandling((responseData) => {
        if (responseData.status !== 'DONE') return { summary: `Scan status: ${responseData?.status || "Unknown"}`, tlp: 'WHITE' };
        const { disposition } = responseData;
        let tlp = 'WHITE';
        if (disposition?.toLowerCase() === 'phish') tlp = 'RED';
        else if (disposition?.toLowerCase() === 'clean') tlp = 'GREEN';
        return { summary: `Disposition: ${disposition || 'N/A'}`, tlp, keyMetric: disposition || 'N/A' };
    }),
  },
  crowdsec: {
    name: 'CrowdSec',
    icon: 'crowdsec_logo_small',
    detailComponent: CrowdSecDetailsComponent,
    requiredKeys: ['crowdsec'],
    supportedIocTypes: ['IPv4'],
    lookupEndpoint: createSingleEndpoint('crowdsec'),
    getSummaryAndTlp: withErrorHandling((responseData) => {
        if (responseData.message?.toLowerCase().includes("not found")) return { summary: "IP not found in CTI", tlp: 'GREEN' };
        const score = responseData.ip_range_score;
        if (score === null || typeof score === 'undefined') return { summary: "Score unavailable", tlp: 'WHITE' };
        const tlp = scoreTlpMapper(score * 100, { red: 80, amber: 50 });
        return { summary: `CTI Range Score: ${score}`, tlp, keyMetric: score };
    }),
  },
  crowdstrike: {
    name: 'CrowdStrike',
    icon: 'crowdstrike_logo',
    detailComponent: CrowdStrikeDetailsComponent,
    requiredKeys: ['crowdstrike_client_id', 'crowdstrike_client_secret'],
    supportedIocTypes: ['IPv4', 'IPv6', 'Domain', 'URL', 'MD5', 'SHA1', 'SHA256', 'Email'],
    lookupEndpoint: createSingleEndpoint('crowdstrike'),
    getSummaryAndTlp: withErrorHandling((responseData) => {
        const indicators = responseData.resources || [];
        if (indicators.length === 0) return { summary: "Not found", tlp: 'GREEN' };
        const malicious = indicators.filter(ind => ind.malicious_confidence === 'high' || ind.malicious_confidence === 'medium').length;
        return { summary: `${indicators.length} indicators found (${malicious} malicious)`, tlp: malicious > 0 ? 'RED' : 'AMBER', keyMetric: indicators.length };
    }),
  },
  emailrepio: {
    name: 'EmailRep.io',
    icon: 'emailrepio_logo_small',
    detailComponent: EmailrepioDetails,
    requiredKeys: ['emailrepio'],
    supportedIocTypes: ['Email'],
    lookupEndpoint: createSingleEndpoint('emailrepio'),
    getSummaryAndTlp: withErrorHandling(withNoDataCheck((responseData) => {
      let tlp = 'GREEN';
      if (responseData.suspicious) tlp = 'RED';
      else if (responseData.reputation === 'low') tlp = 'AMBER';
      return { summary: `Reputation: ${responseData.reputation || 'N/A'}${responseData.suspicious ? ' (Suspicious)' : ''}`, tlp, keyMetric: responseData.reputation };
    })),
  },
  github: {
    name: 'GitHub Search',
    icon: 'github_logo_small',
    detailComponent: GithubDetails,
    requiredKeys: ['github_pat'],
    supportedIocTypes: ['IPv4', 'IPv6', 'Domain', 'URL', 'Email', 'MD5', 'SHA1', 'SHA256', 'CVE'],
    lookupEndpoint: createSingleEndpoint('github'),
    getSummaryAndTlp: withErrorHandling((responseData) => {
        const count = responseData.total_count || 0;
        return { summary: `${count} mention(s)`, tlp: count > 0 ? 'AMBER' : 'GREEN', keyMetric: count };
    }),
  },
  haveibeenpwned: {
    name: 'Have I Been Pwned',
    icon: 'hibp_logo_small',
    detailComponent: HaveibeenpwndDetails,
    requiredKeys: ['hibp_api_key'],
    supportedIocTypes: ['Email'],
    lookupEndpoint: createSingleEndpoint('haveibeenpwned'),
    getSummaryAndTlp: (responseData) => {
        if (responseData?.error === 404) return { summary: "Not found in any breaches", tlp: 'GREEN' };
        if (responseData?.error) return { summary: `Error: ${responseData.message || responseData.error}`, tlp: 'WHITE' };
        const breachCount = responseData.breachedaccount?.length || 0;
        return { summary: `Found in ${breachCount} breach(es)`, tlp: breachCount > 0 ? 'RED' : 'GREEN', keyMetric: breachCount };
    },
  },
  hunterio: {
    name: 'Hunter.io',
    icon: 'hunterio_logo_small',
    detailComponent: HunterioDetails,
    requiredKeys: ['hunterio_api_key'],
    supportedIocTypes: ['Email'],
    lookupEndpoint: createSingleEndpoint('hunterio'),
    getSummaryAndTlp: withErrorHandling(withNoDataCheck((responseData) => {
        const { result, disposable } = responseData.data;
        let tlp = 'GREEN';
        if (disposable || result === 'undeliverable') tlp = 'RED';
        else if (result === 'risky') tlp = 'AMBER';
        return { summary: `Status: ${result}${disposable ? ' (Disposable)' : ''}`, tlp, keyMetric: result };
    }, 'data')),
  },
  ipqualityscore: {
    name: 'IPQualityScore',
    icon: 'ipqualityscore_logo_small',
    detailComponent: IpQualityscoreDetails,
    requiredKeys: ['ipqualityscore'],
    supportedIocTypes: ['IPv4'],
    lookupEndpoint: createSingleEndpoint('ipqualityscore'),
    getSummaryAndTlp: withErrorHandling((responseData) => {
        const score = responseData.fraud_score;
        if (typeof score === 'undefined') return { summary: "No score", tlp: 'WHITE' };
        const tlp = scoreTlpMapper(score, { red: 90, amber: 75 });
        return { summary: `Fraud Score: ${score}`, tlp, keyMetric: score };
    }),
  },
  maltiverse: {
    name: 'Maltiverse',
    icon: 'maltiverse_logo_small',
    detailComponent: MaltiverseDetails,
    requiredKeys: ['maltiverse'],
    supportedIocTypes: ['IPv4', 'Domain', 'URL', 'MD5', 'SHA1', 'SHA256'],
    lookupEndpoint: createSingleEndpoint('maltiverse'),
    getSummaryAndTlp: withErrorHandling((responseData) => {
        const classification = responseData.classification;
        if (!classification) return { summary: "No classification", tlp: 'WHITE' };
        let tlp = 'BLUE';
        if (classification === 'malicious') tlp = 'RED';
        else if (classification === 'suspicious') tlp = 'AMBER';
        else if (classification === 'neutral' || classification === 'whitelist' || classification === 'whitelisted') tlp = 'GREEN';
        return { summary: `Classification: ${classification}`, tlp, keyMetric: classification };
    }),
  },
  malwarebazaar: {
    name: 'MalwareBazaar',
    icon: 'malwarebazaar_logo_small',
    detailComponent: MalwarebazaarDetails,
    requiredKeys: ['malwarebazaar'],
    supportedIocTypes: ['MD5', 'SHA1', 'SHA256'],
    lookupEndpoint: createSingleEndpoint('malwarebazaar'),
    getSummaryAndTlp: withErrorHandling((responseData) => {
        const status = responseData.query_status;
        if (status === 'hash_not_found') return { summary: "Hash not found", tlp: 'GREEN' };
        if (status === 'ok') return { summary: `Found: ${responseData.data[0].signature || 'Malware Sample'}`, tlp: 'RED', keyMetric: responseData.data[0].signature };
        return { summary: `Status: ${status}`, tlp: 'WHITE' };
    }),
  },
  mandiant: {
    name: 'Mandiant',
    icon: 'mandiant_logo',
    detailComponent: MandiantDetails,
    requiredKeys: ['mandiant_key', 'mandiant_secret'],
    supportedIocTypes: ['IPv4', 'IPv6', 'Domain', 'URL', 'MD5', 'SHA1', 'SHA256', 'Email'],
    lookupEndpoint: createSingleEndpoint('mandiant'),
    getSummaryAndTlp: withErrorHandling((responseData) => {
        if (!responseData?.indicators) return { summary: "No data", tlp: 'GREEN' };
        const score = responseData.indicators[0]?.mscore;
        let tlp = 'BLUE';
        if (score >= 70) tlp = 'RED'; else if (score >= 40) tlp = 'AMBER';
        return { summary: `Risk Score: ${score || 'N/A'}`, tlp, keyMetric: score };
    }),
  },
  nistnvd: {
    name: 'NIST NVD',
    icon: 'nistnvd_logo_small',
    detailComponent: NistNvdDetailsComponent,
    requiredKeys: ['nist_nvd_api_key'],
    supportedIocTypes: ['CVE'],
    lookupEndpoint: createSingleEndpoint('nistnvd'),
    getSummaryAndTlp: withErrorHandling((responseData) => {
        if (!responseData.vulnerabilities?.length) return { summary: "CVE not found", tlp: 'GREEN' };
        const cve = responseData.vulnerabilities[0].cve;
        const metrics = cve.metrics?.cvssMetricV31 || cve.metrics?.cvssMetricV30 || [];
        const severity = metrics[0]?.cvssData?.baseSeverity || 'UNKNOWN';
        let tlp = 'WHITE';
        if (severity === 'CRITICAL' || severity === 'HIGH') tlp = 'RED';
        else if (severity === 'MEDIUM') tlp = 'AMBER';
        else if (severity === 'LOW') tlp = 'BLUE';
        return { summary: `Severity: ${severity}`, tlp, keyMetric: severity };
    }),
  },
  pulsedive: {
    name: 'Pulsedive',
    icon: 'pulsedive_logo_small',
    detailComponent: PulsediveDetails,
    requiredKeys: ['pulsedive'],
    supportedIocTypes: ['IPv4', 'Domain', 'MD5', 'SHA1', 'SHA256', 'URL'],
    lookupEndpoint: createSingleEndpoint('pulsedive'),
    getSummaryAndTlp: (responseData) => {
        if (responseData?.error === 404) return { summary: "Not found", tlp: 'GREEN' };
        if (responseData?.error) return { summary: `Error: ${responseData.error.info}`, tlp: 'WHITE' };
        const risk = responseData.risk?.toLowerCase() || 'unknown';
        let tlp = 'WHITE';
        if (risk === 'critical' || risk === 'high') tlp = 'RED';
        else if (risk === 'medium') tlp = 'AMBER';
        else if (risk === 'low') tlp = 'BLUE';
        else if (risk === 'none') tlp = 'GREEN';
        return { summary: `Risk: ${risk}`, tlp, keyMetric: risk };
    },
  },
  reddit: {
    name: 'Reddit Search',
    icon: 'reddit_logo_small',
    detailComponent: RedditDetails,
    requiredKeys: ['reddit_client_id', 'reddit_client_secret'],
    supportedIocTypes: ['IPv4', 'IPv6', 'Domain', 'URL', 'Email', 'MD5', 'SHA1', 'SHA256', 'CVE'],
    lookupEndpoint: createSingleEndpoint('reddit'),
    getSummaryAndTlp: withErrorHandling((responseData) => {
        const count = responseData?.count || responseData?.posts?.length || 0;
        return { summary: `${count} mention(s)`, tlp: count > 0 ? 'AMBER' : 'GREEN', keyMetric: count };
    }),
  },
  safeBrowse: {
    name: 'Google Safe Browse',
    icon: 'safeBrowse_logo_small',
    detailComponent: SafeBrowseDetails,
    requiredKeys: ['safeBrowse'],
    supportedIocTypes: ['Domain', 'URL'],
    lookupEndpoint: createSingleEndpoint('safeBrowse'),
    getSummaryAndTlp: withErrorHandling((responseData) => {
        if (!responseData.matches?.length) return { summary: "Clean", tlp: 'GREEN' };
        const threats = responseData.matches.map(m => m.threatType).join(', ');
        return { summary: `Threat(s) found: ${threats}`, tlp: 'RED', keyMetric: threats };
    }),
  },
  shodan: {
    name: 'Shodan',
    icon: 'shodan_logo_small',
    detailComponent: ShodanDetailsComponent,
    requiredKeys: ['shodan'],
    supportedIocTypes: ['IPv4', 'Domain'],
    lookupEndpoint: createSingleEndpoint('shodan'),
    getSummaryAndTlp: (responseData) => {
        if (responseData?.error === 404) return { summary: "No results found", tlp: 'WHITE' };
        if (responseData?.error) return { summary: `Error: ${responseData.message || responseData.error}`, tlp: 'WHITE' };
        if (!responseData || Object.keys(responseData).length <= 1) return { summary: "No information", tlp: 'WHITE' };
        const portCount = responseData.ports?.length || 0;
        const vuln_count = responseData.vulns?.length || 0;
        let tlp = 'GREEN';
        if (vuln_count > 0) tlp = 'AMBER';
        return { summary: `${portCount} open port(s), ${vuln_count} vulnerability(s)`, tlp, keyMetric: `${portCount}/${vuln_count}` };
    },
  },
  threatfox: {
    name: 'ThreatFox',
    icon: 'threatfox_logo_small',
    detailComponent: ThreatfoxDetails,
    requiredKeys: ['threatfox'],
    supportedIocTypes: ['IPv4', 'IPv6', 'Domain', 'URL', 'MD5', 'SHA1', 'SHA256'],
    lookupEndpoint: createSingleEndpoint('threatfox'),
    getSummaryAndTlp: withErrorHandling((responseData) => {
        if (responseData.query_status === 'no_result') return { summary: "Not found", tlp: 'GREEN' };
        if (responseData.query_status === 'ok') return { summary: `Threat: ${responseData.data[0].threat_type}`, tlp: 'RED', keyMetric: responseData.data[0].threat_type };
        return { summary: `Status: ${responseData.query_status}`, tlp: 'WHITE' };
    }),
  },
  twitter: {
    name: 'Twitter/X Search',
    icon: 'twitter_logo_small',
    detailComponent: TwitterDetails,
    requiredKeys: ['twitter_bearer_token'],
    supportedIocTypes: ['IPv4', 'IPv6', 'Domain', 'URL', 'Email', 'MD5', 'SHA1', 'SHA256', 'CVE'],
    lookupEndpoint: createSingleEndpoint('twitter'),
    getSummaryAndTlp: (responseData) => {
        if (responseData?.error) return { summary: `Error: ${responseData.title || responseData.detail}`, tlp: 'WHITE' };
        const count = responseData.meta?.result_count || 0;
        return { summary: `${count} post(s) found`, tlp: count > 0 ? 'AMBER' : 'GREEN', keyMetric: count };
    },
  },
  urlhaus: {
    name: 'URLhaus',
    icon: 'urlhaus_logo_small',
    detailComponent: UrlHausDetails,
    requiredKeys: ['urlhaus'],
    supportedIocTypes: ['URL', 'Domain'],
    lookupEndpoint: createSingleEndpoint('urlhaus'),
    getSummaryAndTlp: withErrorHandling((responseData) => {
        if (responseData.query_status === 'no_results') return { summary: "Not found", tlp: 'GREEN' };
        if (responseData.query_status === 'ok') {
            const status = responseData.url_status || responseData.urls[0].url_status;
            return { summary: `Found, status: ${status}`, tlp: status === 'online' ? 'RED' : 'AMBER', keyMetric: status };
        }
        return { summary: `Status: ${responseData.query_status}`, tlp: 'WHITE' };
    }),
  },
  urlscanio: {
    name: 'URLScan.io',
    icon: 'urlscanio_logo_small', 
    detailComponent: UrlScanDetails, 
    requiredKeys: [],
    supportedIocTypes: ['Domain', 'URL', 'IPv4'],
    lookupEndpoint: createSingleEndpoint('urlscanio'), 
    getSummaryAndTlp: withErrorHandling((responseData) => {
      const results = responseData?.results;
      if (!results || results.length === 0) {
        return { summary: "No scans found", tlp: 'GREEN' };
      }

      const totalScans = results.length;

      const suspiciousTags = ['phishing', 'malware', '@phish_report'];

      const flaggedCount = results.filter(scan => {
        if (scan.verdicts?.overall?.malicious) {
          return true;
        }
        const scanTags = scan.task?.tags || [];
        return scanTags.some(tag => suspiciousTags.includes(tag.toLowerCase()));
      }).length;

      let summary = `${totalScans} scan(s) found`;
      let tlp = 'AMBER';
      let keyMetric = `${flaggedCount}/${totalScans}`;

      if (flaggedCount > 0) {
        summary = `${totalScans} scan(s), ${flaggedCount} flagged`;
        tlp = 'RED';
      }

      return { summary, tlp, keyMetric };
    }),
  },
  virustotal: {
    name: 'VirusTotal',
    icon: 'vt_logo_small',
    detailComponent: VirustotalDetailsComponent,
    requiredKeys: ['virustotal'],
    supportedIocTypes: ['IPv4', 'IPv6', 'Domain', 'URL', 'MD5', 'SHA1', 'SHA256'],
    lookupEndpoint: createSingleEndpoint('virustotal'),
    getSummaryAndTlp: (responseData) => {
      if (responseData?.notFound) return { summary: "Not found", tlp: 'GREEN' };
      if (responseData?.error) {
        const message = responseData.message || String(responseData.error);
        if (message.toLowerCase().includes('not found')) return { summary: "Not found", tlp: 'GREEN' };
        return { summary: `Error: ${message}`, tlp: 'WHITE' };
      }
      const stats = responseData.data?.attributes?.last_analysis_stats;
      if (!stats) return { summary: "No analysis data", tlp: 'WHITE' };
      const malicious = stats.malicious || 0;
      const suspicious = stats.suspicious || 0;
      const total = (stats.harmless || 0) + malicious + suspicious + (stats.timeout || 0) + (stats.undetected || 0);
      let tlp = 'GREEN';
      if (malicious > 0) tlp = 'RED';
      else if (suspicious > 0) tlp = 'AMBER';
      return { summary: `Detected as malicious or suspicious by ${malicious + suspicious}/${total} engines`, tlp, keyMetric: `${malicious + suspicious}/${total}` };
    },
  },
};

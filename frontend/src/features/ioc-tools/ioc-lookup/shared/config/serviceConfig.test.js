import { SERVICE_DEFINITIONS as S } from './serviceConfig';

// Each provider's getSummaryAndTlp turns a raw lookup response into the verdict colour the
// analyst sees first - these pin the thresholds and the "not found" vs "error" distinction.
const verdict = (key, data) => S[key].getSummaryAndTlp(data);
const tlp = (key, data) => verdict(key, data).tlp;

describe('SERVICE_DEFINITIONS shape', () => {
  it.each(Object.entries(S))('%s is fully declared', (_key, def) => {
    expect(def.name).toEqual(expect.any(String));
    expect(Array.isArray(def.requiredKeys)).toBe(true);
    expect(def.supportedIocTypes.length).toBeGreaterThan(0);
    expect(typeof def.getSummaryAndTlp).toBe('function');
    expect(def.detailComponent).toBeTruthy();
  });

  it('lookup endpoints URL-encode the IOC and type', () => {
    expect(S.virustotal.lookupEndpoint('http://a.b/?x=1&y=2', 'URL')).toBe(
      '/api/ioc/lookup/virustotal?ioc=http%3A%2F%2Fa.b%2F%3Fx%3D1%26y%3D2&ioc_type=URL',
    );
  });

  it.each(Object.keys(S).filter((k) => !['haveibeenpwned', 'pulsedive', 'shodan', 'twitter', 'virustotal'].includes(k)))(
    '%s maps a backend error to a WHITE error verdict',
    (key) => {
      expect(verdict(key, { error: 500, message: 'upstream down' })).toEqual({ summary: 'Error: upstream down', tlp: 'WHITE' });
    },
  );
});

describe('score-based providers', () => {
  it.each([
    [0, 'GREEN'], [24, 'GREEN'], [25, 'AMBER'], [74, 'AMBER'], [75, 'RED'], [100, 'RED'],
  ])('AbuseIPDB %i%% -> %s', (score, expected) => {
    expect(verdict('abuseipdb', { data: { abuseConfidenceScore: score } })).toEqual({
      summary: `Abuse Score: ${score}%`, tlp: expected, keyMetric: `${score}%`,
    });
  });

  it('AbuseIPDB without data is WHITE no-data', () => {
    expect(verdict('abuseipdb', {})).toEqual({ summary: 'No data available', tlp: 'WHITE' });
  });

  it.each([
    [0, 'GREEN'], [1, 'GREEN'], [2, 'GREEN'], [3, 'AMBER'], [4, 'RED'], [5, 'RED'],
  ])('CrowdSec range score %i/5 -> %s', (score, expected) => {
    // Regression: the 0-5 score was multiplied by 100, so any score >= 1 read as RED.
    expect(tlp('crowdsec', { ip_range_score: score })).toBe(expected);
  });

  it('CrowdSec not-found and missing score', () => {
    expect(tlp('crowdsec', { message: 'IP address Not Found' })).toBe('GREEN');
    expect(verdict('crowdsec', {})).toEqual({ summary: 'Score unavailable', tlp: 'WHITE' });
    expect(verdict('crowdsec', { ip_range_score: 0 }).summary).toBe('CTI Range Score: 0/5');
  });

  it.each([[39, 'GREEN'], [40, 'AMBER'], [75, 'RED']])('FFraud IP %i -> %s', (score, expected) => {
    expect(tlp('ffraud', { fraud_score: score })).toBe(expected);
  });

  it.each([[74, 'GREEN'], [75, 'AMBER'], [89, 'AMBER'], [90, 'RED']])('IPQS %i -> %s', (score, expected) => {
    expect(tlp('ipqualityscore', { fraud_score: score })).toBe(expected);
  });

  it('IPQS without a score', () => {
    expect(tlp('ipqualityscore', {})).toBe('WHITE');
  });

  it.each([['0.05', 'GREEN', '5.00%'], ['0.10', 'AMBER', '10.00%'], ['0.5', 'RED', '50.00%']])(
    'EPSS %s -> %s',
    (epss, expected, pct) => {
      expect(verdict('firstepss', { data: [{ epss }] })).toEqual(expect.objectContaining({ tlp: expected, summary: `EPSS: ${pct}` }));
    },
  );

  it('EPSS with no entry', () => {
    expect(tlp('firstepss', { data: [] })).toBe('WHITE');
  });

  it.each([[undefined, 'BLUE'], [39, 'BLUE'], [40, 'AMBER'], [70, 'RED']])('Mandiant mscore %s -> %s', (mscore, expected) => {
    expect(tlp('mandiant', { indicators: [{ mscore }] })).toBe(expected);
  });

  it('Mandiant with no indicators is GREEN', () => {
    expect(tlp('mandiant', {})).toBe('GREEN');
  });
});

describe('VirusTotal', () => {
  const stats = (s) => ({ data: { attributes: { last_analysis_stats: s } } });

  it('counts malicious+suspicious over all engines', () => {
    expect(verdict('virustotal', stats({ harmless: 60, malicious: 3, suspicious: 1, undetected: 6, timeout: 0 }))).toEqual({
      summary: 'Detected as malicious or suspicious by 4/70 engines', tlp: 'RED', keyMetric: '4/70',
    });
    expect(tlp('virustotal', stats({ harmless: 70, suspicious: 1 }))).toBe('AMBER');
    expect(tlp('virustotal', stats({ harmless: 70 }))).toBe('GREEN');
  });

  it('not-found is GREEN, other errors and missing stats WHITE', () => {
    expect(tlp('virustotal', { notFound: true })).toBe('GREEN');
    expect(tlp('virustotal', { error: 404, message: 'Resource Not Found' })).toBe('GREEN');
    expect(verdict('virustotal', { error: 429 })).toEqual({ summary: 'Error: 429', tlp: 'WHITE' });
    expect(tlp('virustotal', { data: {} })).toBe('WHITE');
  });
});

describe('status/listing providers', () => {
  it('AlienVault: malware or malicious activity RED, pulses AMBER, otherwise GREEN', () => {
    expect(verdict('alienvault', { pulse_info: { count: 2 }, section_malware: { data: [1, 2, 3] } })).toEqual({
      summary: '2 pulse(s), 3 malware sample(s)', tlp: 'RED', keyMetric: 2,
    });
    expect(tlp('alienvault', { section_reputation: { reputation: { activities: [{ name: 'Malicious Host' }] } } })).toBe('RED');
    expect(tlp('alienvault', { pulse_info: { count: 1 } })).toBe('AMBER');
    expect(tlp('alienvault', { pulse_info: { count: 0 } })).toBe('GREEN');
  });

  it('Blacklist: OFAC beats OpenSanctions beats ScamSniffer', () => {
    expect(verdict('blacklist', { matched: false })).toEqual({ summary: 'No match — not listed', tlp: 'GREEN' });
    expect(verdict('blacklist', { matched: true, sources: ['SCAMSNIFFER', 'OFAC'], ofac: { entity_name: 'Lazarus' } }))
      .toEqual({ summary: 'OFAC SANCTIONED: Lazarus', tlp: 'RED', keyMetric: 'OFAC' });
    expect(verdict('blacklist', { matched: true, sources: ['OPENSANCTIONS'] }).summary).toBe('OpenSanctions match: flagged entity');
    expect(verdict('blacklist', { matched: true, sources: ['SCAMSNIFFER'], scamsniffer: { phishing_domain: 'x.io' } }).summary)
      .toBe('Phishing-associated address (ScamSniffer): x.io');
  });

  it('CheckPhish only judges finished scans', () => {
    expect(tlp('checkphish', { status: 'PENDING' })).toBe('WHITE');
    expect(tlp('checkphish', { status: 'DONE', disposition: 'Phish' })).toBe('RED');
    expect(tlp('checkphish', { status: 'DONE', disposition: 'clean' })).toBe('GREEN');
    expect(tlp('checkphish', { status: 'DONE', disposition: 'suspicious' })).toBe('WHITE');
  });

  it('CISA KEV', () => {
    expect(tlp('cisakev', { listed: false })).toBe('GREEN');
    expect(verdict('cisakev', { listed: true, knownRansomwareCampaignUse: 'Known' }).summary).toBe('Actively exploited — known ransomware use');
  });

  it('CrowdStrike: high/medium confidence means RED', () => {
    expect(tlp('crowdstrike', { resources: [] })).toBe('GREEN');
    expect(tlp('crowdstrike', { resources: [{ malicious_confidence: 'low' }] })).toBe('AMBER');
    expect(verdict('crowdstrike', { resources: [{ malicious_confidence: 'medium' }, {}] }).summary).toBe('2 indicators found (1 malicious)');
  });

  it('EmailRep / FFraud email / Hunter', () => {
    expect(tlp('emailrepio', { suspicious: true, reputation: 'high' })).toBe('RED');
    expect(tlp('emailrepio', { reputation: 'low' })).toBe('AMBER');
    expect(tlp('emailrepio', { reputation: 'high' })).toBe('GREEN');
    expect(verdict('ffraudemail', { is_disposable: true }).summary).toBe('Disposable email domain');
    expect(tlp('ffraudemail', { community_blacklisted: true })).toBe('RED');
    expect(tlp('ffraudemail', { valid_format: false })).toBe('AMBER');
    expect(verdict('ffraudemail', { valid_format: true, safe_domain: true }).summary).toBe('Safe domain');
    expect(tlp('hunterio', { data: { result: 'undeliverable' } })).toBe('RED');
    expect(tlp('hunterio', { data: { result: 'risky' } })).toBe('AMBER');
    expect(verdict('hunterio', { data: { result: 'deliverable', disposable: true } })).toEqual(
      expect.objectContaining({ tlp: 'RED', summary: 'Status: deliverable (Disposable)' }),
    );
  });

  it('HIBP: 404 means clean, breaches RED', () => {
    expect(tlp('haveibeenpwned', { error: 404 })).toBe('GREEN');
    expect(tlp('haveibeenpwned', { error: 401, message: 'bad key' })).toBe('WHITE');
    expect(verdict('haveibeenpwned', { breachedaccount: [{}, {}] }).summary).toBe('Found in 2 breach(es)');
    expect(tlp('haveibeenpwned', { breachedaccount: [] })).toBe('GREEN');
  });

  it('Hudson Rock: domain shape vs email/IP shape', () => {
    expect(tlp('hudsonrock', { data: [], total: 0 })).toBe('GREEN');
    expect(tlp('hudsonrock', { data: [], total: 5, employees: 2 })).toBe('RED');
    expect(tlp('hudsonrock', { data: [], total: 5, employees: 0 })).toBe('AMBER');
    expect(tlp('hudsonrock', { stealers: [{}] })).toBe('RED');
    expect(tlp('hudsonrock', { stealers: [] })).toBe('GREEN');
  });

  it('LeakIX: leaks RED, services only GREEN, nothing WHITE', () => {
    expect(tlp('leakix', { Leaks: [{}], Services: [] })).toBe('RED');
    expect(verdict('leakix', { Services: [{}, {}] })).toEqual(expect.objectContaining({ tlp: 'GREEN', summary: '2 service(s), no leaks' }));
    expect(tlp('leakix', {})).toBe('WHITE');
  });

  it('Library of Leaks', () => {
    expect(tlp('libraryofleaks', { total_hits: 0 })).toBe('GREEN');
    expect(verdict('libraryofleaks', { total_hits: 3, collections: [1] }).summary).toBe('3 mention(s) across 1 collection(s)');
  });

  it.each([
    ['malicious', 'RED'], ['suspicious', 'AMBER'], ['neutral', 'GREEN'], ['whitelisted', 'GREEN'], ['other', 'BLUE'],
  ])('Maltiverse %s -> %s', (classification, expected) => {
    expect(tlp('maltiverse', { classification })).toBe(expected);
  });

  it('abuse.ch providers', () => {
    expect(tlp('malwarebazaar', { query_status: 'hash_not_found' })).toBe('GREEN');
    expect(verdict('malwarebazaar', { query_status: 'ok', data: [{ signature: 'AgentTesla' }] }).summary).toBe('Found: AgentTesla');
    expect(tlp('malwarebazaar', { query_status: 'illegal_hash' })).toBe('WHITE');
    expect(tlp('threatfox', { query_status: 'no_result' })).toBe('GREEN');
    expect(verdict('threatfox', { query_status: 'ok', data: [{ threat_type: 'botnet_cc' }] }).tlp).toBe('RED');
    // a malformed ok-response (empty data) must not throw out of the result row's render
    expect(verdict('threatfox', { query_status: 'ok', data: [] })).toEqual({ summary: 'Threat: unknown', tlp: 'RED', keyMetric: undefined });
    expect(verdict('malwarebazaar', { query_status: 'ok' }).summary).toBe('Found: Malware Sample');
    expect(tlp('urlhaus', { query_status: 'no_results' })).toBe('GREEN');
    expect(verdict('urlhaus', { query_status: 'ok', url_status: 'online' })).toEqual(expect.objectContaining({ tlp: 'RED', summary: 'Found, status: online' }));
    expect(verdict('urlhaus', { query_status: 'ok', urls: [{ url_status: 'offline' }, { url_status: 'online' }] }).summary)
      .toBe('Found, 2 URL(s), status: online');
    expect(tlp('urlhaus', { query_status: 'ok', urls: [{ url_status: 'offline' }] })).toBe('AMBER');
  });

  it.each([
    ['CRITICAL', 'RED'], ['HIGH', 'RED'], ['MEDIUM', 'AMBER'], ['LOW', 'BLUE'], [undefined, 'WHITE'],
  ])('NVD severity %s -> %s', (baseSeverity, expected) => {
    const data = { vulnerabilities: [{ cve: { metrics: { cvssMetricV31: [{ cvssData: { baseSeverity } }] } } }] };
    expect(tlp('nistnvd', data)).toBe(expected);
  });

  it('NVD falls back to CVSS 3.0 and reports a missing CVE as GREEN', () => {
    expect(tlp('nistnvd', { vulnerabilities: [{ cve: { metrics: { cvssMetricV30: [{ cvssData: { baseSeverity: 'HIGH' } }] } } }] })).toBe('RED');
    expect(tlp('nistnvd', { vulnerabilities: [] })).toBe('GREEN');
  });

  it('OpenPhish / Safe Browsing', () => {
    expect(tlp('openphish', { listed: true })).toBe('RED');
    expect(tlp('openphish', { listed: false })).toBe('GREEN');
    expect(verdict('safeBrowse', { matches: [{ threatType: 'MALWARE' }, { threatType: 'SOCIAL_ENGINEERING' }] }).summary)
      .toBe('Threat(s) found: MALWARE, SOCIAL_ENGINEERING');
    expect(tlp('safeBrowse', {})).toBe('GREEN');
  });

  it.each([['critical', 'RED'], ['medium', 'AMBER'], ['low', 'BLUE'], ['none', 'GREEN'], ['weird', 'WHITE']])(
    'Pulsedive %s -> %s', (risk, expected) => {
      expect(tlp('pulsedive', { risk })).toBe(expected);
    },
  );

  it('Pulsedive errors', () => {
    expect(tlp('pulsedive', { error: 404 })).toBe('GREEN');
    expect(verdict('pulsedive', { error: { info: 'rate limited' } }).summary).toBe('Error: rate limited');
  });

  it('Shodan: vulns AMBER, ports only GREEN, empty WHITE', () => {
    expect(verdict('shodan', { ip_str: '1.1.1.1', ports: [80, 443], vulns: ['CVE-1'] })).toEqual({
      summary: '2 open port(s), 1 vulnerability(s)', tlp: 'AMBER', keyMetric: '2/1',
    });
    expect(tlp('shodan', { ip_str: 'x', ports: [22] })).toBe('GREEN');
    expect(tlp('shodan', { ip_str: 'x' })).toBe('WHITE');
    expect(tlp('shodan', { error: 404 })).toBe('WHITE');
  });

  it('mention counters (GitHub, Reddit, Twitter)', () => {
    expect(tlp('github', { total_count: 0 })).toBe('GREEN');
    expect(tlp('github', { total_count: 3 })).toBe('AMBER');
    expect(verdict('reddit', { posts: [{}, {}] }).summary).toBe('2 mention(s)');
    expect(tlp('twitter', { meta: { result_count: 1 } })).toBe('AMBER');
    expect(verdict('twitter', { error: true, title: 'Unauthorized' }).summary).toBe('Error: Unauthorized');
  });

  it('URLScan: flagged by verdict or tag', () => {
    expect(tlp('urlscanio', { results: [] })).toBe('GREEN');
    expect(verdict('urlscanio', { results: [{}, {}] })).toEqual({ summary: '2 scan(s) found', tlp: 'AMBER', keyMetric: '0/2' });
    expect(verdict('urlscanio', {
      results: [{ verdicts: { overall: { malicious: true } } }, { task: { tags: ['Phishing'] } }, {}],
    })).toEqual({ summary: '3 scan(s), 2 flagged', tlp: 'RED', keyMetric: '2/3' });
  });
});

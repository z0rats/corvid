import api from '../../../../core/services/baseApi';
import { newsfeedSettingsApi } from './settingsApi';

vi.mock('../../../../core/services/baseApi', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}));

afterEach(() => vi.clearAllMocks());

describe('newsfeedSettingsApi.getConfig', () => {
  it('requests the newsfeed config', async () => {
    api.get.mockResolvedValue({ data: { autoFetch: true } });

    const result = await newsfeedSettingsApi.getConfig();

    expect(api.get).toHaveBeenCalledWith('/api/settings/newsfeed/config');
    expect(result).toEqual({ autoFetch: true });
  });
});

describe('newsfeedSettingsApi.updateConfig', () => {
  it('puts the updated config', async () => {
    api.put.mockResolvedValue({ data: { autoFetch: false } });

    const result = await newsfeedSettingsApi.updateConfig({ autoFetch: false });

    expect(api.put).toHaveBeenCalledWith('/api/settings/newsfeed/config', { autoFetch: false });
    expect(result).toEqual({ autoFetch: false });
  });
});

describe('newsfeedSettingsApi.getCtiSettings', () => {
  it('requests CTI settings', async () => {
    api.get.mockResolvedValue({ data: { enrichment: true } });

    const result = await newsfeedSettingsApi.getCtiSettings();

    expect(api.get).toHaveBeenCalledWith('/api/settings/cti');
    expect(result).toEqual({ enrichment: true });
  });
});

describe('newsfeedSettingsApi.updateCtiSettings', () => {
  it('wraps the settings payload under a settings key', async () => {
    api.put.mockResolvedValue({ data: { enrichment: false } });

    const result = await newsfeedSettingsApi.updateCtiSettings({ enrichment: false });

    expect(api.put).toHaveBeenCalledWith('/api/settings/cti', { settings: { enrichment: false } });
    expect(result).toEqual({ enrichment: false });
  });
});

describe('newsfeedSettingsApi.getKeywords', () => {
  it('requests the keyword list', async () => {
    api.get.mockResolvedValue({ data: [{ id: 1, keyword: 'ransomware' }] });

    const result = await newsfeedSettingsApi.getKeywords();

    expect(api.get).toHaveBeenCalledWith('/api/settings/keywords');
    expect(result).toEqual([{ id: 1, keyword: 'ransomware' }]);
  });
});

describe('newsfeedSettingsApi.addKeyword', () => {
  it('posts the new keyword', async () => {
    api.post.mockResolvedValue({ data: { id: 2, keyword: 'phishing' } });

    const result = await newsfeedSettingsApi.addKeyword('phishing');

    expect(api.post).toHaveBeenCalledWith('/api/settings/keywords', { keyword: 'phishing' });
    expect(result).toEqual({ id: 2, keyword: 'phishing' });
  });
});

describe('newsfeedSettingsApi.deleteKeyword', () => {
  it('deletes the keyword by id', async () => {
    api.delete.mockResolvedValue({});

    await newsfeedSettingsApi.deleteKeyword(2);

    expect(api.delete).toHaveBeenCalledWith('/api/settings/keywords/2');
  });
});

describe('newsfeedSettingsApi.getNewsfeeds', () => {
  it('requests the configured newsfeeds', async () => {
    api.get.mockResolvedValue({ data: [{ name: 'thehackernews' }] });

    const result = await newsfeedSettingsApi.getNewsfeeds();

    expect(api.get).toHaveBeenCalledWith('/api/settings/modules/newsfeed');
    expect(result).toEqual([{ name: 'thehackernews' }]);
  });
});

describe('newsfeedSettingsApi.addNewsfeed', () => {
  it('posts the new feed', async () => {
    api.post.mockResolvedValue({ data: { name: 'newfeed' } });

    const result = await newsfeedSettingsApi.addNewsfeed({ name: 'newfeed', url: 'https://x.test/rss' });

    expect(api.post).toHaveBeenCalledWith('/api/settings/modules/newsfeed', {
      name: 'newfeed',
      url: 'https://x.test/rss',
    });
    expect(result).toEqual({ name: 'newfeed' });
  });
});

describe('newsfeedSettingsApi.deleteNewsfeed', () => {
  it('deletes the feed by URL-encoded name', async () => {
    api.delete.mockResolvedValue({});

    await newsfeedSettingsApi.deleteNewsfeed('feed name/1');

    expect(api.delete).toHaveBeenCalledWith('/api/settings/modules/newsfeed?feed_name=feed%20name%2F1');
  });
});

describe('newsfeedSettingsApi.enableNewsfeed', () => {
  it('patches the feed as enabled', async () => {
    api.patch.mockResolvedValue({});

    await newsfeedSettingsApi.enableNewsfeed('feed name');

    expect(api.patch).toHaveBeenCalledWith('/api/settings/modules/newsfeed/feed%20name', { enabled: true });
  });
});

describe('newsfeedSettingsApi.disableNewsfeed', () => {
  it('patches the feed as disabled', async () => {
    api.patch.mockResolvedValue({});

    await newsfeedSettingsApi.disableNewsfeed('feed name');

    expect(api.patch).toHaveBeenCalledWith('/api/settings/modules/newsfeed/feed%20name', { enabled: false });
  });
});

describe('newsfeedSettingsApi.validateFeed', () => {
  it('posts the feed for validation', async () => {
    api.post.mockResolvedValue({ data: { valid: true } });

    const result = await newsfeedSettingsApi.validateFeed({ url: 'https://x.test/rss' });

    expect(api.post).toHaveBeenCalledWith('/api/settings/modules/newsfeed/validation', {
      url: 'https://x.test/rss',
    });
    expect(result).toEqual({ valid: true });
  });
});

describe('newsfeedSettingsApi.uploadFeedIcon', () => {
  it('puts the icon as multipart form data', async () => {
    api.put.mockResolvedValue({ data: { iconUrl: '/icons/feed.png' } });
    const formData = new FormData();

    const result = await newsfeedSettingsApi.uploadFeedIcon('feed%20name', formData);

    expect(api.put).toHaveBeenCalledWith('/api/settings/modules/newsfeed/feed%20name/icon', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    expect(result).toEqual({ iconUrl: '/icons/feed.png' });
  });
});

describe('newsfeedSettingsApi.deleteFeedIcon', () => {
  it('deletes the feed icon', async () => {
    api.delete.mockResolvedValue({ data: { success: true } });

    const result = await newsfeedSettingsApi.deleteFeedIcon('feed%20name');

    expect(api.delete).toHaveBeenCalledWith('/api/settings/modules/newsfeed/feed%20name/icon');
    expect(result).toEqual({ success: true });
  });
});

describe('newsfeedSettingsApi.refetchFeedIcon', () => {
  it('posts to refetch a single feed icon', async () => {
    api.post.mockResolvedValue({ data: { iconUrl: '/icons/feed.png' } });

    const result = await newsfeedSettingsApi.refetchFeedIcon('feed%20name');

    expect(api.post).toHaveBeenCalledWith('/api/settings/modules/newsfeed/feed%20name/icon/refetch');
    expect(result).toEqual({ iconUrl: '/icons/feed.png' });
  });
});

describe('newsfeedSettingsApi.refetchAllMissingIcons', () => {
  it('posts to refetch all missing icons', async () => {
    api.post.mockResolvedValue({ data: { refetched: 3 } });

    const result = await newsfeedSettingsApi.refetchAllMissingIcons();

    expect(api.post).toHaveBeenCalledWith('/api/settings/modules/newsfeed/icons/refetch-missing');
    expect(result).toEqual({ refetched: 3 });
  });
});

describe('newsfeedSettingsApi.getBlacklistEntries', () => {
  it('requests all entries when no type filter is given', async () => {
    api.get.mockResolvedValue({ data: [] });

    const result = await newsfeedSettingsApi.getBlacklistEntries();

    expect(api.get).toHaveBeenCalledWith('/api/settings/newsfeed/trends-blacklist');
    expect(result).toEqual([]);
  });

  it('appends a type filter when given', async () => {
    api.get.mockResolvedValue({ data: [] });

    await newsfeedSettingsApi.getBlacklistEntries('word');

    expect(api.get).toHaveBeenCalledWith('/api/settings/newsfeed/trends-blacklist?type=word');
  });
});

describe('newsfeedSettingsApi.addBlacklistEntry', () => {
  it('posts the value and type', async () => {
    api.post.mockResolvedValue({ data: { id: 1 } });

    const result = await newsfeedSettingsApi.addBlacklistEntry('the', 'word');

    expect(api.post).toHaveBeenCalledWith('/api/settings/newsfeed/trends-blacklist', {
      value: 'the',
      type: 'word',
    });
    expect(result).toEqual({ id: 1 });
  });
});

describe('newsfeedSettingsApi.deleteBlacklistEntry', () => {
  it('deletes the blacklist entry by id', async () => {
    api.delete.mockResolvedValue({});

    await newsfeedSettingsApi.deleteBlacklistEntry(1);

    expect(api.delete).toHaveBeenCalledWith('/api/settings/newsfeed/trends-blacklist/1');
  });
});

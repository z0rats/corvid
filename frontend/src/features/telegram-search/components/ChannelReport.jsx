import { useTranslation } from 'react-i18next';

import ChannelOverviewCard from './ChannelOverviewCard';
import ActivityMetricsCard from './ActivityMetricsCard';
import ChannelNetworkCard from './ChannelNetworkCard';
import IndicatorsCard from './IndicatorsCard';
import PostsTable from './PostsTable';

/** A scan's whole `result` blob - shared by the live scan view and the history detail. */
export default function ChannelReport({ result, disabled }) {
  const { t } = useTranslation('telegramSearch');
  if (!result?.profile) return null;

  return (
    <>
      <ChannelOverviewCard profile={result.profile} />
      {result.metrics && <ActivityMetricsCard metrics={result.metrics} />}
      {result.metrics && <ChannelNetworkCard metrics={result.metrics} disabled={disabled} />}
      <IndicatorsCard indicators={result.indicators} />
      <PostsTable title={t('posts.topTitle')} posts={result.top_posts} />
      <PostsTable title={t('posts.sampledTitle', { count: result.posts?.length ?? 0 })} posts={result.posts} />
    </>
  );
}

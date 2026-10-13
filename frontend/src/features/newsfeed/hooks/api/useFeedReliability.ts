import { useEffect, useState } from 'react';
import { newsfeedSettingsApi } from '../../services/api/settingsApi';
import type { Reliability } from '../../constants/reliability';

/** Feed name -> reliability grade for every graded feed. Empty until loaded, and on failure:
 * a missing grade only hides the badge, so it must never break the article list. */
export function useFeedReliability(): Record<string, Reliability> {
  const [grades, setGrades] = useState<Record<string, Reliability>>({});

  useEffect(() => {
    let ignore = false;
    newsfeedSettingsApi
      .getNewsfeeds()
      .then((feeds: Array<{ name: string; reliability?: Reliability }>) => {
        if (ignore) return;
        const next: Record<string, Reliability> = {};
        feeds.forEach((feed) => {
          if (feed.reliability) next[feed.name] = feed.reliability;
        });
        setGrades(next);
      })
      .catch(() => {});
    return () => {
      ignore = true;
    };
  }, []);

  return grades;
}

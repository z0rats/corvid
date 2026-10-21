import { METRIC_GROUPS } from "./metricsConfig";

// Value code -> display label per metric key, derived from the same config the
// selects render so an exported value always reads like the UI shows it.
export const METRIC_MAPS = Object.fromEntries(
  Object.values(METRIC_GROUPS)
    .flat()
    .map(({ key, options }) => [key, Object.fromEntries(options.map(({ value, label }) => [value, label]))]),
);

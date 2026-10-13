// Admiralty-system source reliability grades (backend: `SourceReliability`). F means the
// source cannot be judged, not that it is the worst.
export const RELIABILITY_GRADES = ['A', 'B', 'C', 'D', 'E', 'F'] as const;

export type Reliability = (typeof RELIABILITY_GRADES)[number];

// "Minimum reliability" options: F is "cannot be judged", not a step below E, so it's no
// threshold - the backend accepts only A-E and leaves F feeds out of any filtered view.
export const MIN_RELIABILITY_OPTIONS: Reliability[] = ['A', 'B', 'C', 'D', 'E'];

// The app theme maps `success` and `info` to the same blue, so green (`primary`) marks the
// trusted grades and blue the middle one; amber/red/grey follow.
type ChipColor = 'primary' | 'info' | 'warning' | 'error' | 'default';

export const RELIABILITY_COLORS: Record<Reliability, ChipColor> = {
  A: 'primary',
  B: 'primary',
  C: 'info',
  D: 'warning',
  E: 'error',
  F: 'default',
};

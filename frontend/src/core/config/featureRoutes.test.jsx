import { describe, it, expect } from 'vitest';
import { FEATURE_ROUTES } from './featureRoutes';

describe('FEATURE_ROUTES', () => {
  it('mounts every feature page at its documented path', () => {
    expect(FEATURE_ROUTES.map((r) => r.path)).toEqual([
      'newsfeed/*',
      'settings/*',
      'ai-templates/*',
      'ioc-tools/*',
      'email-analyzer/*',
      'image-tools/*',
      'cvss-calculator/*',
      'rules/*',
      'username-search/*',
      'email-search/*',
      'reddit-search/*',
      'dork-runner/*',
      'git-recon/*',
      'amass/*',
      'ru-business-check/*',
      'youtube/*',
      'steam-recon/*',
      'instagram-search/*',
      'phone-search/*',
      'sanctions-search/*',
      'investigations/*',
    ]);
  });

  it('has a component for every path', () => {
    for (const { Component } of FEATURE_ROUTES) expect(Component).toBeTruthy();
  });
});

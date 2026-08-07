// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
	site: 'https://z0rats.github.io',
	base: '/corvid',
	integrations: [
		starlight({
			title: 'Corvid',
			description: 'Self-hostable OSINT/security-analyst toolkit',
			social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/z0rats/corvid' }],
			editLink: {
				baseUrl: 'https://github.com/z0rats/corvid/edit/main/website/',
			},
			sidebar: [
				{
					label: 'Getting Started',
					items: [
						{ label: 'Introduction', slug: 'getting-started/introduction' },
						{ label: 'Installation', slug: 'getting-started/installation' },
						{ label: 'Configuration', slug: 'getting-started/configuration' },
						{ label: 'Settings Reference', slug: 'getting-started/settings-reference' },
						{ label: 'Backup & Operational Security', slug: 'getting-started/backup-and-operations' },
						{ label: 'Local Development', slug: 'getting-started/local-development' },
						{ label: 'Troubleshooting', slug: 'getting-started/troubleshooting' },
					],
				},
				{
					label: 'Usage',
					items: [
						{ label: 'Command Palette', slug: 'usage/command-palette' },
					],
				},
				{
					label: 'Architecture',
					items: [
						{ label: 'Backend', slug: 'architecture/backend' },
						{ label: 'Frontend', slug: 'architecture/frontend' },
						{ label: 'Security', slug: 'architecture/security' },
						{ label: 'AI / LLM Providers', slug: 'architecture/ai-providers' },
						{ label: 'Reports & Exports', slug: 'architecture/reports' },
					],
				},
				{
					label: 'Features',
					items: [
						{ label: 'Newsfeed', slug: 'features/newsfeed' },
						{ label: 'IOC Tools', slug: 'features/ioc-tools' },
						{ label: 'Email Analyzer', slug: 'features/email-analyzer' },
						{ label: 'Image Tools', slug: 'features/image-tools' },
						{ label: 'Username Search', slug: 'features/username-search' },
						{ label: 'Email Search', slug: 'features/email-search' },
						{ label: 'Reddit Search', slug: 'features/reddit-search' },
						{ label: 'Git Recon', slug: 'features/git-recon' },
						{ label: 'Dork Runner', slug: 'features/dork-runner' },
						{ label: 'YouTube', slug: 'features/youtube' },
						{ label: 'LLM Templates', slug: 'features/llm-templates' },
						{ label: 'CVSS Calculator', slug: 'features/cvss-calculator' },
						{ label: 'Rule Creator', slug: 'features/rule-creator' },
						{ label: 'Browser Extension', slug: 'features/browser-extension' },
					],
				},
			],
		}),
	],
});

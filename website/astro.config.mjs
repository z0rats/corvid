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
					items: [{ autogenerate: { directory: 'getting-started' } }],
				},
				{
					label: 'Usage',
					items: [{ autogenerate: { directory: 'usage' } }],
				},
				{
					label: 'Architecture',
					items: [{ autogenerate: { directory: 'architecture' } }],
				},
				{
					label: 'Features',
					items: [{ autogenerate: { directory: 'features' } }],
				},
			],
		}),
	],
});

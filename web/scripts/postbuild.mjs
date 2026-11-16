// Post-build: things a static host would need that SvelteKit doesn't emit itself.
//   1. .assetsignore so wrangler doesn't upload _worker.js as a static asset
//   2. sitemap.xml + robots.txt pointing at it
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const dir = '.svelte-kit/cloudflare';
const site = (process.env.SITE_URL || 'https://campboard.wwangjunling7.workers.dev').replace(/\/$/, '');

writeFileSync(join(dir, '.assetsignore'), '_worker.js\n', 'utf8');

const snap = JSON.parse(readFileSync('src/lib/data/snapshot.json', 'utf8'));
const today = snap.generated.slice(0, 10);

const urls = [
	{ loc: `${site}/`, changefreq: 'hourly', priority: '1.0' },
	{ loc: `${site}/changes`, changefreq: 'hourly', priority: '0.8' },
	...snap.campgrounds.map((c) => ({
		loc: `${site}/campground/${c.id}`,
		changefreq: 'hourly',
		priority: '0.7'
	}))
];

const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls
	.map(
		(u) =>
			`\t<url><loc>${u.loc}</loc><lastmod>${today}</lastmod><changefreq>${u.changefreq}</changefreq><priority>${u.priority}</priority></url>`
	)
	.join('\n')}
</urlset>
`;
writeFileSync(join(dir, 'sitemap.xml'), sitemap, 'utf8');

writeFileSync(
	join(dir, 'robots.txt'),
	`User-agent: *\nAllow: /\n\nSitemap: ${site}/sitemap.xml\n`,
	'utf8'
);

console.log(`postbuild: .assetsignore, sitemap (${urls.length} urls), robots.txt`);

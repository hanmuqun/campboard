# campboard web

The public site. SvelteKit 3 + `@sveltejs/adapter-cloudflare`, deployed as a Cloudflare Worker with static assets.

## How the data gets here

Nothing in this folder talks to Recreation.gov. The Python side does:

```
python ../fetch.py --workers 2     # writes ../data/snapshot.json + ../data/changes.json
npm run build                      # copies that JSON in, prerenders every page
npm run deploy                     # uploads to Cloudflare
```

`scripts/sync-data.mjs` copies `../data/*.json` into `src/lib/data/` (bundled into the pages) and into `static/data.json` (the open-data link in the footer).

## Local

```
npm run dev        # http://localhost:5173
npm run build      # prerenders 25 pages into .svelte-kit/cloudflare
npm run preview    # serves the production build on :4173
```

## Deploy

```
.\deploy.ps1
```

or by hand: `npx wrangler login` once, then `npm run deploy`.

First deploy publishes to `campboard.<your-subdomain>.workers.dev`. If that name is taken, change `name` in `wrangler.jsonc`.

## Notes for future me

- Every page is prerendered (`+layout.js` sets `prerender = true`). Refreshing data means rebuilding and redeploying. Once data moves to D1, the campground pages should switch to on-demand rendering and only the static pages stay prerendered.
- `scripts/postbuild.mjs` writes `.assetsignore` so `_worker.js` is not uploaded as a static asset.
- SvelteKit 3 differences that bit me: no `svelte.config.js` (config goes in `vite.config.ts`), `#lib` instead of `$lib` (needs the `imports` map in `package.json`).

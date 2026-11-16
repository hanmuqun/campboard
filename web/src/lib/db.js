// Reads the board from D1. Falls back to the JSON snapshot that ships with the
// build, so the site never renders empty if the database is missing or empty.
//
// SvelteKit 3 + adapter-cloudflare no longer passes `platform` at runtime: the
// bindings are reachable through the `cloudflare:workers` module instead.
import { env as cfEnv } from 'cloudflare:workers';
import snapshot from './data/snapshot.json';
import changeLog from './data/changes.json';

const TTL = 60_000;
let cache = { at: 0, data: null };

function fromJson() {
	return {
		camps: snapshot.campgrounds,
		changes: changeLog,
		generated: snapshot.generated,
		source: 'json'
	};
}

function shapeCamp(r) {
	return {
		id: r.id,
		name: r.name,
		park: r.park,
		city: r.city,
		state: r.state,
		url: r.url,
		sites: r.sites,
		days: JSON.parse(r.days)
	};
}

function shapeChange(r) {
	return {
		ts: r.ts,
		id: r.camp_id,
		name: r.name,
		park: r.park,
		date: r.date,
		kind: r.kind,
		before: r.before,
		after: r.after,
		delta: r.delta
	};
}

export async function getData(platform) {
	const now = Date.now();
	if (cache.data && now - cache.at < TTL) return cache.data;

	const db = platform?.env?.DB ?? cfEnv?.DB;
	if (!db) return fromJson();

	try {
		const [camps, changes, meta] = await Promise.all([
			db.prepare('SELECT * FROM campgrounds ORDER BY park, name').all(),
			db.prepare('SELECT * FROM changes ORDER BY ts DESC LIMIT 400').all(),
			db.prepare("SELECT v FROM meta WHERE k = 'generated'").first()
		]);

		if (!camps.results?.length) return fromJson();

		const data = {
			camps: camps.results.map(shapeCamp),
			changes: (changes.results ?? []).map(shapeChange),
			generated: meta?.v ?? '',
			source: 'd1'
		};
		cache = { at: now, data };
		return data;
	} catch (err) {
		console.error('d1 read failed, using bundled snapshot:', err);
		return fromJson();
	}
}

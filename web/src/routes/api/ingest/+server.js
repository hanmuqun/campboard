import { env } from 'cloudflare:workers';

const json = (body, status = 200) =>
	new Response(JSON.stringify(body), {
		status,
		headers: { 'content-type': 'application/json', 'x-robots-tag': 'noindex' }
	});

// Constant-time-ish comparison so a wrong key cannot be guessed byte by byte.
function same(a, b) {
	if (typeof a !== 'string' || typeof b !== 'string' || a.length !== b.length) return false;
	let diff = 0;
	for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
	return diff === 0;
}

// The fetcher (local machine now, GitHub Actions later) posts its snapshot here.
// Everything it would otherwise need wrangler + a Cloudflare API token for.
export async function POST({ request }) {
	const expected = env?.INGEST_KEY || '';
	if (!expected) return json({ error: 'ingest key not configured' }, 503);
	if (!same(request.headers.get('x-ingest-key') || '', expected)) {
		return json({ error: 'unauthorized' }, 401);
	}

	let body;
	try {
		body = await request.json();
	} catch {
		return json({ error: 'body is not json' }, 400);
	}

	const camps = Array.isArray(body?.campgrounds) ? body.campgrounds : null;
	const changes = Array.isArray(body?.changes) ? body.changes : [];
	if (!camps || typeof body.generated !== 'string') {
		return json({ error: 'expected generated + campgrounds' }, 400);
	}

	const db = env?.DB;
	if (!db) return json({ error: 'no database binding' }, 500);

	const stmts = [db.prepare('DELETE FROM campgrounds')];
	for (const c of camps) {
		stmts.push(
			db
				.prepare(
					'INSERT INTO campgrounds (id,name,park,city,state,url,sites,days,updated_at) VALUES (?,?,?,?,?,?,?,?,?)'
				)
				.bind(
					c.id,
					c.name ?? null,
					c.park ?? null,
					c.city ?? null,
					c.state ?? null,
					c.url ?? null,
					c.sites ?? null,
					JSON.stringify(c.days ?? {}),
					body.generated
				)
		);
	}
	for (const e of changes) {
		stmts.push(
			db
				.prepare(
					'INSERT OR IGNORE INTO changes (ts,camp_id,name,park,date,kind,before,after,delta) VALUES (?,?,?,?,?,?,?,?,?)'
				)
				.bind(e.ts, e.id, e.name ?? null, e.park ?? null, e.date, e.kind, e.before ?? null, e.after ?? null, e.delta ?? null)
		);
	}
	stmts.push(
		db
			.prepare("INSERT INTO meta (k,v) VALUES ('generated',?) ON CONFLICT(k) DO UPDATE SET v=excluded.v")
			.bind(body.generated)
	);

	for (let i = 0; i < stmts.length; i += 40) {
		await db.batch(stmts.slice(i, i + 40));
	}

	return json({ ok: true, campgrounds: camps.length, changes: changes.length, generated: body.generated });
}

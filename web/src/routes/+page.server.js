import { getData } from '#lib/db';

export async function load({ platform, setHeaders }) {
	const data = await getData(platform);
	setHeaders({ 'cache-control': 'public, max-age=30, s-maxage=60' });
	return { camps: data.camps, changes: data.changes, generated: data.generated };
}

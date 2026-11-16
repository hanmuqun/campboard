import { error } from '@sveltejs/kit';
import { getData } from '#lib/db';

export async function load({ params, platform, setHeaders }) {
	const data = await getData(platform);
	const camp = data.camps.find((c) => c.id === params.id);
	if (!camp) error(404, 'No such campground');

	setHeaders({ 'cache-control': 'public, max-age=30, s-maxage=60' });
	return {
		camp,
		changes: data.changes.filter((c) => c.id === camp.id).slice(0, 8),
		generated: data.generated
	};
}

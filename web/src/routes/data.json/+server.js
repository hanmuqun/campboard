import { getData } from '#lib/db';

// The same snapshot the board renders, for anyone who wants the raw data.
// Served from D1 so it cannot drift away from the pages.
export async function GET({ platform, setHeaders }) {
	const data = await getData(platform);
	setHeaders({
		'content-type': 'application/json; charset=utf-8',
		'cache-control': 'public, max-age=60, s-maxage=120'
	});
	return new Response(
		JSON.stringify({ generated: data.generated, campgrounds: data.camps }, null, '\t')
	);
}

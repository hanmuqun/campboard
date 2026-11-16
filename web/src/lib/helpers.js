// Pure helpers. No data imports here: every page gets its rows from db.js.

export function bookable(row) {
	return row ? row.available + row.reserved : 0;
}

export function ratio(row) {
	const book = bookable(row);
	return book ? row.available / book : 0;
}

export function addDays(d, n) {
	const copy = new Date(d.getTime());
	copy.setUTCDate(copy.getUTCDate() + n);
	return copy;
}

export function iso(d) {
	return d.toISOString().slice(0, 10);
}

export function todayFrom(generated) {
	return new Date(`${(generated || new Date().toISOString()).slice(0, 10)}T00:00:00Z`);
}

export function fmtShort(dateStr) {
	const d = new Date(`${dateStr}T00:00:00Z`);
	return d.toLocaleDateString('en-GB', {
		weekday: 'short',
		day: '2-digit',
		month: 'short',
		timeZone: 'UTC'
	});
}

export function fmtDayNum(dateStr) {
	const d = new Date(`${dateStr}T00:00:00Z`);
	return d.toLocaleDateString('en-GB', { month: 'short', day: 'numeric', timeZone: 'UTC' });
}

export function daysFrom(camp, start, n) {
	const out = [];
	for (let i = 0; i < n; i++) {
		const key = iso(addDays(start, i));
		out.push({ date: key, row: camp.days[key] });
	}
	return out;
}

export function pillFor(row) {
	// No row means "we did not get an answer", not "this night is full". Those
	// are different facts and the board must not conflate them.
	if (!row) return { cls: 'p-unknown', text: 'n/a' };
	// A date the park has not put on sale yet is not "closed" either.
	if (row.unreleased) return { cls: 'p-unreleased', text: 'soon' };
	if (bookable(row) === 0) return { cls: 'p-closed', text: 'closed' };
	if (row.available === 0) return { cls: 'p-zero', text: '0' };
	return { cls: ratio(row) < 0.34 ? 'p-low' : 'p-ok', text: String(row.available) };
}

export function weekend(today) {
	const d = today.getUTCDay();
	const until = 6 - d || 7;
	const sat = addDays(today, until);
	return { sat: iso(sat), sun: iso(addDays(sat, 1)) };
}

export function when(ts) {
	return ts.slice(0, 16).replace('T', ' ');
}

export function what(e) {
	if (e.kind === 'released') return `went from closed to ${e.after} free`;
	if (e.kind === 'season_closed') return `closed for the season (was ${e.before} free)`;
	if (e.kind === 'sold_out') return `sold out (was ${e.before} free)`;
	const n = Math.abs(e.delta ?? e.after - e.before);
	const sites = `${n} free site${n === 1 ? '' : 's'}`;
	return e.kind === 'taken' ? `lost ${sites} to ${e.after} left` : `gained ${sites} to ${e.after} left`;
}

<script>
	import {
		todayFrom, daysFrom, bookable, ratio, fmtShort, fmtDayNum, when, what
	} from '#lib/helpers';

	let { data } = $props();
	const camp = data.camp;
	const generated = data.generated;
	const today = todayFrom(generated);

	const d21 = daysFrom(camp, today, 21);

	const cells = d21.map(({ date, row }) => {
		if (!row || bookable(row) === 0) return { date, cls: 'gone', val: '\u2014' };
		if (row.available === 0) return { date, cls: 'free0', val: '0' };
		return { date, cls: ratio(row) < 0.34 ? 'free1' : 'free2', val: String(row.available) };
	});

	const nxt = d21.map((d) => d.row).filter((r) => r && bookable(r));
	const openDays = nxt.filter((r) => r.available > 0).length;
	const totalAvail = nxt.reduce((s, r) => s + r.available, 0);

	const summary = nxt.length
		? `${openDays} of the next 21 nights have at least one free site. ${totalAvail} site-nights available in total.`
		: 'This campground is closed for the season in the window shown.';

	const week = d21.slice(0, 7);
</script>

<svelte:head>
	<title>{camp.name} availability — {camp.park}</title>
	<meta
		name="description"
		content="Live campsite availability for {camp.name} in {camp.park}: free sites per night for the next three weeks, read from Recreation.gov."
	/>
</svelte:head>

<p class="sub"><a href="/">&larr; all campgrounds</a></p>
<h2 style="margin-top:0">{camp.park}</h2>
<p class="lede">{camp.name}</p>
<p class="sub">
	{summary} Last refreshed {generated.replace('T', ' ').replace('+00:00', '')} (UTC).
</p>

<h2>Next 21 nights</h2>
<div class="daygrid">
	{#each cells as c}
		<div class="day {c.cls}">
			<div class="d">{fmtDayNum(c.date)}</div>
			<div class="n">{c.val}</div>
		</div>
	{/each}
</div>
<p class="legend">
	Free sites per night:
	<span style="background:var(--grey)"></span>closed
	<span style="background:var(--red)"></span>0
	<span style="background:var(--amber)"></span>few
	<span style="background:var(--green)"></span>plenty
</p>

<h2>First week, in detail</h2>
<table>
	<thead>
		<tr>
			<th>Night</th><th class="num">Free</th><th class="num">Booked</th>
			<th class="num">Closed / not yet released</th>
		</tr>
	</thead>
	<tbody>
		{#each week as { date, row }}
			<tr>
				<td>{fmtShort(date)}</td>
				{#if !row || bookable(row) === 0}
					<td class="num">closed</td><td class="num">&mdash;</td><td class="num">&mdash;</td>
				{:else}
					<td class="num">{row.available}</td>
					<td class="num">{row.reserved}</td>
					<td class="num">{row.closed + row.nyr}</td>
				{/if}
			</tr>
		{/each}
	</tbody>
</table>

{#if data.changes.length}
	<h2>Recent changes here</h2>
	<table>
		<thead><tr><th class="num">When</th><th class="num">Night</th><th>What</th></tr></thead>
		<tbody>
			{#each data.changes as e}
				<tr>
					<td class="num nowrap">{when(e.ts)}</td>
					<td class="num nowrap">{fmtShort(e.date)}</td>
					<td>{what(e)}</td>
				</tr>
			{/each}
		</tbody>
	</table>
{/if}

<div class="card" style="margin-top:30px">
	<h3>Book it on Recreation.gov</h3>
	<p class="meta">The official reservation page for {camp.name}.</p>
	<a class="btn" href={camp.url} rel="nofollow">Open on Recreation.gov &rarr;</a>
</div>

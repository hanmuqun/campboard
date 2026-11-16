<script>
	import {
		todayFrom, weekend, daysFrom, bookable, pillFor, fmtDayNum, when
	} from '#lib/helpers';

	let { data } = $props();
	const { camps, changes, generated } = data;

	const today = todayFrom(generated);
	const todayKey = today.toISOString().slice(0, 10);
	const { sat, sun } = weekend(today);

	let openWeekend = 0;
	let soldOutWeekend = 0;
	let closedWeekend = 0;

	const rows = camps.map((c) => {
		const d7 = daysFrom(c, today, 7);
		const avail7 = d7.reduce((sum, { row }) => sum + (row ? row.available : 0), 0);
		const wk = [c.days[sat], c.days[sun]];
		const wkAvail = wk.reduce((sum, r) => sum + (r ? r.available : 0), 0);
		const wkBook = wk.reduce((sum, r) => sum + bookable(r), 0);

		if (wkBook === 0) closedWeekend++;
		else if (wkAvail === 0) soldOutWeekend++;
		else openWeekend++;

		return { camp: c, avail7, d7 };
	});

	const fresh = changes.filter((c) => c.kind === 'opened' || c.kind === 'released').slice(0, 6);

	// 23 rows is small enough that filtering in the browser is instant and needs
	// no search index, no extra request, and no third-party service.
	let q = $state('');
	let box;

	const filtered = $derived.by(() => {
		const needle = q.trim().toLowerCase();
		if (!needle) return rows;
		return rows.filter(({ camp }) =>
			`${camp.name} ${camp.park} ${camp.state ?? ''}`.toLowerCase().includes(needle)
		);
	});

	function onKey(e) {
		const typing = ['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName);
		if (e.key === '/' && !typing) {
			e.preventDefault();
			box?.focus();
		} else if (e.key === 'Escape' && typing) {
			q = '';
			box?.blur();
		}
	}

	function barClass(row) {
		if (!row || bookable(row) === 0) return 'p-closed';
		return row.available === 0 ? 'p-zero' : 'p-ok';
	}
</script>

<svelte:window onkeydown={onKey} />

<svelte:head>
	<title>Campboard — live US campsite availability, one page</title>
	<meta
		name="description"
		content="How many campsites are still free tonight and this weekend at Yosemite, Zion, Joshua Tree, Yellowstone and more. Read straight from Recreation.gov."
	/>
</svelte:head>

<p class="lede">
	{rows.length} of the busiest campgrounds in the US national parks, and how many sites each one still
	has free &mdash; so you can stop opening 40 tabs.
</p>
<p class="sub">
	Last refreshed {generated.replace('T', ' ').replace('+00:00', '')} (UTC). This weekend: {openWeekend}
	campgrounds have space, {soldOutWeekend} are full, {closedWeekend} are closed for the season.
</p>

{#if fresh.length}
	<h2>Just opened</h2>
	<ul class="fresh">
		{#each fresh as e}
			<li>
				{when(e.ts)} UTC &middot; <a href="/campground/{e.id}">{e.name}</a> &middot;
				{fmtDayNum(e.date)} &mdash; {e.kind === 'released' ? 'opened with' : 'now has'}
				<b>{e.after}</b> free
			</li>
		{/each}
	</ul>
{/if}

<div class="searchbar">
	<h2>Availability, soonest first</h2>
	<input
		bind:this={box}
		bind:value={q}
		type="search"
		placeholder="Filter by campground or park  ( / )"
		aria-label="Filter campgrounds by name or park"
	/>
</div>
{#if q.trim()}
	<p class="count">Showing {filtered.length} of {rows.length}</p>
{/if}
{#if filtered.length === 0}
	<p class="empty">Nothing matches &ldquo;{q.trim()}&rdquo;. Try the park name instead.</p>
{:else}
	<table>
		<thead>
			<tr>
				<th>Campground</th>
				<th class="num">Tonight</th>
				<th class="num">Sat</th>
				<th class="num">Sun</th>
				<th class="num">7 days</th>
				<th class="hide-s">Next 7 nights</th>
			</tr>
		</thead>
		<tbody>
			{#each filtered as { camp, avail7, d7 } (camp.id)}
				{@const tonight = pillFor(camp.days[todayKey])}
				{@const satPill = pillFor(camp.days[sat])}
				{@const sunPill = pillFor(camp.days[sun])}
				<tr>
					<td class="camp">
						<a href="/campground/{camp.id}">{camp.name}</a>
						<div class="park">{camp.park}</div>
					</td>
					<td class="num"><span class="pill {tonight.cls}">{tonight.text}</span></td>
					<td class="num"><span class="pill {satPill.cls}">{satPill.text}</span></td>
					<td class="num"><span class="pill {sunPill.cls}">{sunPill.text}</span></td>
					<td class="num">{avail7 || "—"}</td>
					<td class="hide-s nowrap">
						{#each d7 as { row }}
							<span
								class="pill {barClass(row)}"
								style="min-width:0;padding:2px 5px;font-size:11px"
							>{row && bookable(row) > 0 ? row.available : ''}</span>
						{/each}
					</td>
				</tr>
			{/each}
		</tbody>
	</table>
{/if}
<p class="lede" style="margin-top:26px">
	Each number is free tent/RV sites for that night. Closed means closed for the season, not booked.
</p>

<script>
	import { when, fmtShort, what } from '#lib/helpers';

	let { data } = $props();
	const { changes, generated } = data;
	const opens = changes.filter((c) => c.kind === 'opened' || c.kind === 'released');
</script>

<svelte:head>
	<title>Campsite changes — what just opened on Campboard</title>
	<meta
		name="description"
		content="A running log of campsite availability changes across US national park campgrounds: nights that opened up, campgrounds that closed for the season, weekends that sold out."
	/>
</svelte:head>

<p class="lede" style="max-width:none">
	Every night that changed on this board, newest first. Logged by comparing each refresh with the
	one before it &mdash; the only public record of campsites quietly coming back.
</p>
<p class="sub">
	Last refreshed {generated.replace('T', ' ').replace('+00:00', '')} (UTC). {changes.length} events
	logged so far, {opens.length} of them sites appearing.
</p>

<h2>Changes</h2>
<table>
	<thead>
		<tr>
			<th class="num">When</th><th class="num">Night</th><th>Campground</th><th>What</th>
		</tr>
	</thead>
	<tbody>
		{#each changes.slice(0, 200) as e}
			<tr>
				<td class="num nowrap">{when(e.ts)}</td>
				<td class="num nowrap">{fmtShort(e.date)}</td>
				<td><a href="/campground/{e.id}">{e.name}</a></td>
				<td>{what(e)}</td>
			</tr>
		{:else}
			<tr>
				<td colspan="4">
					Nothing yet. The board has to be refreshed twice before anything can change.
				</td>
			</tr>
		{/each}
	</tbody>
</table>

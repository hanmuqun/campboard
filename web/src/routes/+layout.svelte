<script>
	import '../app.css';
	let { children } = $props();
</script>

<header>
	<div class="wrap">
		<h1><a href="/">Campboard</a></h1>
		<p>Campsite availability for US national parks &middot; <a href="/changes">what just opened</a></p>
		<div style="margin-left:auto;display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:#c3cad2" aria-label="What the colours mean">
			<span style="display:inline-flex;align-items:center;gap:5px;white-space:nowrap"
				><i style="width:11px;height:11px;border-radius:3px;background:#bbf7d0"></i>plenty free</span
			>
			<span style="display:inline-flex;align-items:center;gap:5px;white-space:nowrap"
				><i style="width:11px;height:11px;border-radius:3px;background:#fde68a"></i>few free</span
			>
			<span style="display:inline-flex;align-items:center;gap:5px;white-space:nowrap"
				><i style="width:11px;height:11px;border-radius:3px;background:#fecaca"></i>full (0)</span
			>
			<span style="display:inline-flex;align-items:center;gap:5px;white-space:nowrap"
				><i style="width:11px;height:11px;border-radius:3px;background:#e5e7eb"></i>closed by park</span
			>
			<span style="display:inline-flex;align-items:center;gap:5px;white-space:nowrap"
				><i style="width:11px;height:11px;border-radius:3px;border:1px dashed #9ca3af"></i>no data</span
			>
		</div>
	</div>
</header>

<main>
	<div class="wrap">
		{@render children()}
	</div>
</main>

<footer>
	<div class="wrap">
		Not affiliated with Recreation.gov or the National Park Service. Availability is read from
		public Recreation.gov data and may lag the real booking system by minutes. Book through the
		official site. &middot; <a href="/data.json">data.json</a>
	</div>
</footer>

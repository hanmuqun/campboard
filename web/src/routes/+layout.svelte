<script>
	import '../app.css';
	let { children } = $props();
</script>

<header>
	<div class="wrap">
		<h1><a href="/">Campboard</a></h1>
		<p>Campsite availability for US national parks &middot; <a href="/changes">what just opened</a></p>
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

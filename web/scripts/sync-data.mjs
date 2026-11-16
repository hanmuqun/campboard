// Copies the data the Python pipeline produces into the web app before each build.
// The Python side stays the only thing that talks to Recreation.gov.
import { copyFileSync, mkdirSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const src = join(here, '..', '..', 'data');
const out = join(here, '..', 'src', 'lib', 'data');

mkdirSync(out, { recursive: true });

for (const file of ['snapshot.json', 'changes.json']) {
	const from = join(src, file);
	if (!existsSync(from)) {
		console.warn(`skip ${file}: not built yet`);
		continue;
	}
	copyFileSync(from, join(out, file));
	console.log(`synced ${file}`);
}

// a public copy of the raw snapshot, so /data.json is a real file
const snap = join(src, 'snapshot.json');
if (existsSync(snap)) {
	const pub = join(here, '..', 'static');
	mkdirSync(pub, { recursive: true });
	copyFileSync(snap, join(pub, 'data.json'));
	console.log('synced static/data.json');
}

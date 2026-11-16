-- campboard schema. Idempotent: safe to apply on every deploy.
CREATE TABLE IF NOT EXISTS campgrounds (
	id         TEXT PRIMARY KEY,
	name       TEXT NOT NULL,
	park       TEXT NOT NULL,
	city       TEXT,
	state      TEXT,
	url        TEXT,
	sites      INTEGER,
	days       TEXT NOT NULL,
	updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS changes (
	ts      TEXT NOT NULL,
	camp_id TEXT NOT NULL,
	name    TEXT NOT NULL,
	park    TEXT NOT NULL,
	date    TEXT NOT NULL,
	kind    TEXT NOT NULL,
	before  INTEGER NOT NULL,
	after   INTEGER NOT NULL,
	delta   INTEGER,
	PRIMARY KEY (ts, camp_id, date, kind)
);

CREATE INDEX IF NOT EXISTS changes_ts ON changes (ts DESC);

CREATE TABLE IF NOT EXISTS meta (
	k TEXT PRIMARY KEY,
	v TEXT NOT NULL
);

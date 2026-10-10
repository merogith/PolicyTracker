import sqlite3
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class StorageBlueprint(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.executescript((ROOT / "architecture/v2/storage.sql").read_text(encoding="utf-8"))
        self.db.execute("INSERT INTO corpus_snapshot VALUES ('c','KAZ',1,?, '{}')", ('a'*64,))

    def tearDown(self):
        self.db.close()

    def bundle(self, kind, country='KAZ', bundle_id='b'):
        self.db.execute("INSERT INTO analysis_run(id,kind,feature,country_code,corpus_snapshot_id,owner_scope,idempotency_key,model_settings_json,state) VALUES (?,?,?,?,'c','team',?,'{}','complete')", (bundle_id,kind,kind,country,bundle_id))
        self.db.execute("INSERT INTO validation_receipt VALUES (?,?,?,'passed','test','{}')", (bundle_id,bundle_id,'b'*64))
        self.db.execute("INSERT INTO report_bundle VALUES (?,?,?,?,?,?,'{}','2026-10-08')", (bundle_id,bundle_id,kind,country,'b'*64,bundle_id))

    def test_automatic_prime_needs_no_human_approval(self):
        self.bundle('prime')
        self.db.execute("INSERT INTO prime_selection VALUES ('KAZ','latest_successful','b',1,'team-member','2026-10-08')")

    def test_ad_hoc_cannot_be_prime(self):
        self.bundle('ad_hoc')
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO prime_selection VALUES ('KAZ','pinned','b',1,'member','2026-10-08')")

    def test_wrong_country_cannot_be_prime(self):
        self.bundle('prime')
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO prime_selection VALUES ('KGZ','pinned','b',1,'member','2026-10-08')")

    def test_bundle_cannot_mutate(self):
        self.bundle('prime')
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE report_bundle SET manifest_json='changed'")

    def test_source_revision_does_not_replace_old_version(self):
        for value in ('a', 'b'):
            self.db.execute("INSERT INTO source_blob VALUES (?, ?, 10)", (value*64,value))
            self.db.execute("INSERT INTO document_version VALUES (?,?,'same-family','{}','event')", (value,value*64))
        self.assertEqual(self.db.execute("SELECT count(*) FROM document_version").fetchone()[0], 2)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE document_version SET blob_sha256=? WHERE id='a'", ('b'*64,))


if __name__ == "__main__":
    unittest.main()

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tracker

class TrackerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.catalog_file = root / "produkte.json"
        self.output_file = root / "docs" / "data" / "prices.json"
        self.output_file.parent.mkdir(parents=True)
        self.catalog = [{"id":"lego-1","name":"LEGO Testset","category":"Kinderspielzeug",
                         "offers":[{"shop":"Shop A","url":"https://shop.example.org/lego"}]}]
        self.catalog_file.write_text(json.dumps(self.catalog))
        self.output_file.write_text(json.dumps({"products":[],"alerts":[],"history":{}}))
        self.patches = [patch.object(tracker,"CONFIG",self.catalog_file),
                        patch.object(tracker,"OUTPUT",self.output_file)]
        for p in self.patches: p.start()
    def tearDown(self):
        for p in self.patches: p.stop()
        self.temp.cleanup()
    def test_first_measurement(self):
        d=tracker.scan(fetch=lambda url,selector:9999,send=lambda a:None)
        self.assertEqual(d["products"][0]["best_price_cents"],9999)
        self.assertEqual(len(d["alerts"]),0)
    def test_price_drop(self):
        tracker.scan(fetch=lambda url,selector:10000,send=lambda a:None)
        d=tracker.scan(fetch=lambda url,selector:7500,send=lambda a:None)
        self.assertEqual(d["alerts"][0]["drop_pct"],25)
    def test_blocked_shop_keeps_last_price(self):
        tracker.scan(fetch=lambda url,selector:7500,send=lambda a:None)
        def fail(*args): raise ValueError("blockiert")
        d=tracker.scan(fetch=fail,send=lambda a:None)
        self.assertFalse(d["products"][0]["fresh"])
        self.assertEqual(d["products"][0]["best_price_cents"],7500)
    def test_duplicate_ids(self):
        with self.assertRaises(ValueError): tracker.valid_catalog(self.catalog*2)
    def test_multiple_shops(self):
        self.catalog[0]["offers"].append({"shop":"Shop B","url":"https://shop.example.org/lego2"})
        self.catalog_file.write_text(json.dumps(self.catalog))
        d=tracker.scan(fetch=lambda url,selector:900 if url.endswith("lego2") else 1500,send=lambda a:None)
        self.assertEqual(d["products"][0]["best_shop"],"Shop B")
if __name__=="__main__": unittest.main()

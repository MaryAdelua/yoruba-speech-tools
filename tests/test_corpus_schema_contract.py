"""Offline structural contract checks; not a replacement for JSON Schema validation."""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


class CorpusSchemaContractTests(unittest.TestCase):
    def read(self,path):
        return json.loads((ROOT/path).read_text(encoding="utf-8"))

    def test_legacy_contract_retained(self):
        current=self.read("evaluation/supervised_example.schema.json")
        old=self.read("evaluation/supervised_example.v0.1.schema.json")
        self.assertEqual(current["$defs"]["legacy_v01"],{k:v for k,v in old.items() if k not in ("$id","$schema")})

    def test_separate_required_origin_fields(self):
        branches=self.read("evaluation/supervised_example.schema.json")["$defs"]["v02"]["oneOf"]
        natural,ai=branches
        self.assertEqual(natural["properties"]["sample_type"]["const"],"natural_reference")
        self.assertIn("natural_source",natural["required"])
        self.assertNotIn("generation",natural["properties"])
        self.assertEqual(ai["properties"]["sample_type"]["const"],"ai_generated")
        self.assertIn("generation",ai["required"])
        self.assertNotIn("natural_source",ai["properties"])

    def test_existing_record_migration_preserves_evidence(self):
        prior=self.read("evaluation/voice_interactions/supervised_example_001.json")
        new=self.read("evaluation/voice_interactions/supervised_example_001.v0.2.json")
        self.assertEqual(prior["audio"],new["audio"])
        self.assertEqual(prior["human_annotations"],new["human_annotations"])
        self.assertEqual(new["transcript"]["status"],"asr_unverified")
        self.assertEqual(new["analysis_design"]["mode"],"unpaired")
        self.assertIsNone(new["generation"]["model_version"])
        self.assertEqual(len(new["assessment_targets"]),7)
        self.assertTrue(all(v["score"] is None and v["status"]=="UNSCORED" for v in new["assessment_targets"].values()))


if __name__=="__main__": unittest.main()

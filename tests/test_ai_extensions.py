"""Unit tests for ISO 27002 RAG Engine and Unstructured Evidence Parser."""

import unittest
from agent_core.iso_rag import IsoRagEngine, iso_rag
from agent_core.unstructured_evidence import (
    UnstructuredEvidenceParser,
    evaluate_corpus_comparison,
    UNSTRUCTURED_EVIDENCE_CORPUS
)


class TestAiExtensions(unittest.TestCase):

    def test_iso_rag_exact_control_retrieval(self):
        ctrl = iso_rag.get_control("A.6.5")
        self.assertIsNotNone(ctrl)
        self.assertEqual(ctrl["pillar"], "people")
        self.assertIn("Offboarding", ctrl["guidance"])
        self.assertIn("A.6.5", ctrl["title"])

    def test_iso_rag_search_by_keyword(self):
        results = iso_rag.search("mã hóa ổ đĩa bitlocker", top_k=3)
        self.assertTrue(len(results) > 0)
        top_codes = [r["code"] for r in results]
        self.assertTrue("A.8.1" in top_codes or "A.6.7" in top_codes)

    def test_iso_rag_remediation_guidance(self):
        guidance = iso_rag.generate_remediation_guidance(
            finding_type="OFFBOARDING_UNREVOKED_SOFTWARE",
            person_name="Nguyễn Văn Test",
            context={"unrevoked_accounts": "VPN, GitLab"}
        )
        self.assertEqual(guidance["primary_control"], "A.6.5")
        self.assertIn("A.6.5", guidance["regulatory_rationale"])
        self.assertTrue(len(guidance["actionable_steps"]) >= 2)

    def test_unstructured_evidence_parser_offboarding_without_approval(self):
        sample_email = UNSTRUCTURED_EVIDENCE_CORPUS[0]["content"]
        facts = UnstructuredEvidenceParser.extract_facts(sample_email)
        self.assertEqual(facts["person_id"], "HF-010")
        self.assertTrue(facts["offboarding_detected"])
        self.assertTrue(facts["hardware_returned"])
        self.assertFalse(facts["software_revoked"])
        self.assertTrue(facts["unapproved_retention"])
        self.assertIn("A.6.5", facts["detected_violations"])
        self.assertIn("A.8.2", facts["detected_violations"])

    def test_unstructured_evidence_parser_approved_exception(self):
        sample_ticket = UNSTRUCTURED_EVIDENCE_CORPUS[1]["content"]
        facts = UnstructuredEvidenceParser.extract_facts(sample_ticket)
        self.assertEqual(facts["person_id"], "HF-025")
        self.assertFalse(facts["unapproved_retention"])
        # Approved exception does not flag violation
        self.assertEqual(len(facts["detected_violations"]), 0)

    def test_unstructured_evidence_parser_remote_violations(self):
        doc = UNSTRUCTURED_EVIDENCE_CORPUS[2]
        sample_memo = f"{doc['subject']}\n{doc['content']}"
        facts = UnstructuredEvidenceParser.extract_facts(sample_memo)
        self.assertEqual(facts["person_id"], "HF-045")
        self.assertTrue(facts["remote_detected"])
        self.assertTrue(facts["missing_encryption"])
        self.assertTrue(facts["missing_mfa"])
        self.assertIn("A.6.7", facts["detected_violations"])

    def test_corpus_comparison_rule_vs_ai(self):
        benchmark = evaluate_corpus_comparison()
        # The AI NLP engine should strongly outperform rule engine on raw text
        self.assertEqual(benchmark["rule_engine"]["accuracy_on_unstructured"], 25.0)  # only matches empty case
        self.assertEqual(benchmark["ai_nlp_agent"]["accuracy_on_unstructured"], 100.0)
        self.assertEqual(len(benchmark["cases"]), 4)


if __name__ == "__main__":
    unittest.main()

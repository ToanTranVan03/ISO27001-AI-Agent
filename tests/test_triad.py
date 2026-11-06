import unittest
from agent_core.simulation import build_enterprise
from agent_core.triad import analyze_triad, calculate_triad_risk, ISO_27002_CITATIONS


class TriadEngineTests(unittest.TestCase):
    def test_baseline_triad_has_three_pillars_and_no_cross_risks(self):
        enterprise = build_enterprise()
        triad = analyze_triad(enterprise)
        self.assertEqual(triad['focal_pillar'], 'people')
        self.assertIn('people', triad['pillars'])
        self.assertIn('software', triad['pillars'])
        self.assertIn('hardware', triad['pillars'])
        self.assertEqual(triad['pillars']['people']['total_records'], 50)
        self.assertEqual(triad['pillars']['software']['total_accounts'], 200)
        self.assertEqual(triad['pillars']['hardware']['total_devices'], 50)
        self.assertEqual(triad['cross_entity_risks'], [])
        self.assertEqual(triad['metrics']['total_cross_risks'], 0)

    def test_offboarding_propagates_to_software_and_hardware(self):
        enterprise = build_enterprise()
        # Terminate HF-025 without revoking accounts or returning laptop
        person = next(p for p in enterprise['people'] if p['id'] == 'HF-025')
        person['status'] = 'terminated'
        
        triad = analyze_triad(enterprise)
        self.assertGreater(triad['metrics']['total_cross_risks'], 0)
        risk_types = [r['type'] for r in triad['cross_entity_risks']]
        self.assertIn('OFFBOARDING_UNREVOKED_SOFTWARE', risk_types)
        self.assertIn('OFFBOARDING_UNRETURNED_HARDWARE', risk_types)
        
        # Verify CIA impact and high risk score
        offboarding_risk = next(r for r in triad['cross_entity_risks'] if r['type'] == 'OFFBOARDING_UNREVOKED_SOFTWARE')
        self.assertGreaterEqual(offboarding_risk['risk']['risk_score'], 12.0)
        self.assertEqual(offboarding_risk['source_pillar'], 'people')
        self.assertEqual(offboarding_risk['target_pillar'], 'software')

    def test_remote_work_propagates_to_hardware_and_software(self):
        enterprise = build_enterprise()
        person = next(p for p in enterprise['people'] if p['id'] == 'HF-028')
        person['remote'] = True
        # Unencrypted laptop and un-MFA VPN
        device = next(d for d in enterprise['devices'] if d['person_id'] == 'HF-028')
        device['encrypted'] = False
        vpn = next(a for a in enterprise['accounts'] if a['person_id'] == 'HF-028' and a['system'] == 'VPN')
        vpn['mfa'] = False

        triad = analyze_triad(enterprise)
        risk_types = [r['type'] for r in triad['cross_entity_risks']]
        self.assertIn('REMOTE_WORK_VULNERABILITY', risk_types)
        remote_risk = next(r for r in triad['cross_entity_risks'] if r['type'] == 'REMOTE_WORK_VULNERABILITY')
        self.assertIn('A.6.7', remote_risk['controls'])
        self.assertIn('A.8.1', remote_risk['controls'])
        self.assertIn('A.8.5', remote_risk['controls'])

    def test_premature_software_provisioning_without_nda(self):
        enterprise = build_enterprise()
        person = next(p for p in enterprise['people'] if p['id'] == 'HF-010')
        person['nda_signed'] = False
        
        triad = analyze_triad(enterprise)
        risk_types = [r['type'] for r in triad['cross_entity_risks']]
        self.assertIn('ONBOARDING_PREMATURE_SOFTWARE', risk_types)

    def test_role_change_without_software_review(self):
        enterprise = build_enterprise()
        person = next(p for p in enterprise['people'] if p['id'] == 'HF-015')
        person['role'] = 'Điều phối viên'
        person['access_review_required'] = True
        
        triad = analyze_triad(enterprise)
        risk_types = [r['type'] for r in triad['cross_entity_risks']]
        self.assertIn('ROLE_CHANGE_UNREVIEWED_SOFTWARE', risk_types)

    def test_iso_27002_citations_coverage(self):
        for cid in ['A.6.1', 'A.6.2', 'A.6.3', 'A.6.4', 'A.6.5', 'A.6.6', 'A.6.7', 'A.6.8', 'A.8.2', 'A.8.5', 'A.8.1']:
            self.assertIn(cid, ISO_27002_CITATIONS)
            citation = ISO_27002_CITATIONS[cid]
            self.assertIn('clause', citation)
            self.assertIn('cia_impact', citation)
            self.assertIn('guidance', citation)

    def test_department_risk_weighting(self):
        # IT department risk is higher than Sales for the same violation
        risk_it = calculate_triad_risk('A.6.5', 'IT', 'violation')
        risk_sales = calculate_triad_risk('A.6.5', 'Sales', 'violation')
        self.assertGreater(risk_it['risk_score'], risk_sales['risk_score'])


if __name__ == '__main__':
    unittest.main()

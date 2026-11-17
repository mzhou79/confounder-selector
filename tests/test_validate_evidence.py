import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from validate_evidence import validate

class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.data={'question':'Exercise and blood pressure among adults', 'search_log':[{'source':'PubMed','query':'exercise AND blood pressure','date':'2026-11-16'}], 'papers':[{'id':'p1','title':'Example uploaded study (not a real citation)','source_type':'uploaded','access_level':'uploaded_full_text','verification_status':'not_applicable'}], 'candidates':[{'variable':'age','role':'uncertain','rationale':'Requires causal assessment','paper_ids':['p1'],'recommendation':'Assess temporality'}]}
    def test_valid(self): self.assertEqual(validate(self.data),[])
    def test_unknown_reference(self):
        self.data['candidates'][0]['paper_ids']=['p2']
        self.assertTrue(any('unknown paper' in e for e in validate(self.data)))
    def test_invalid_doi(self):
        self.data['papers'][0]['doi']='made-up'
        self.assertTrue(any('DOI' in e for e in validate(self.data)))
    def test_duplicate_ids(self):
        self.data['papers'].append(dict(self.data['papers'][0]))
        self.assertTrue(any('duplicate' in e for e in validate(self.data)))
    def test_invalid_role(self):
        self.data['candidates'][0]['role']='proven confounder'
        self.assertTrue(any('invalid role' in e for e in validate(self.data)))
if __name__=='__main__': unittest.main()

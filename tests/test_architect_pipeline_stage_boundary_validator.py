import importlib.util, json, pathlib, subprocess, sys, tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/check-architect-pipeline-stage-boundary.py'
spec=importlib.util.spec_from_file_location('asb', SCRIPT); asb=importlib.util.module_from_spec(spec); spec.loader.exec_module(asb)

def run(*a): return subprocess.run([sys.executable,str(SCRIPT),*a],cwd=ROOT,text=True,capture_output=True)
def codes(result): return [d['code'] for d in result['diagnostics']]

def test_valid_complete_sequence_passes_and_receipts_are_deterministic():
    v=asb.Validator(ROOT); d=ROOT/'fixtures/architect-pipeline-stage-boundary/valid/complete-sequence'
    first=v.validate_sequence(d); second=v.validate_sequence(d)
    assert first==second; assert first['status']=='valid'; assert len(first['receipts'])==4

def test_t01_to_t06_boundary_schema_failures():
    expected={'T01':'SCHEMA_VALIDATION_FAILED','T02':'SCHEMA_VALIDATION_FAILED','T03':'SCHEMA_VALIDATION_FAILED','T04':'ASB-DUPLICATE-UNKNOWN-ID','T05':'SCHEMA_VALIDATION_FAILED','T06':'SCHEMA_VALIDATION_FAILED'}
    v=asb.Validator(ROOT)
    for case,code in expected.items():
        p=next((ROOT/'fixtures/architect-pipeline-stage-boundary/invalid'/case).glob('*.json'))
        r=v.validate_path(p)
        assert r['status']=='invalid'; assert code in codes(r); assert r['diagnostics'][0]['path'].startswith('$')

def test_sequence_unknown_lineage_and_resolution_rules():
    expected={'T07':'ASB-UNKNOWN-LEDGER-MISSING-UPSTREAM-ID','T08':'ASB-UNKNOWN-RESOLVED-WITHOUT-EVIDENCE','T09':'ASB-CANDIDATE-UNTRACKED-UNKNOWN'}
    v=asb.Validator(ROOT)
    for case,code in expected.items():
        r=v.validate_sequence(ROOT/'fixtures/architect-pipeline-stage-boundary/invalid'/case)
        assert r['status']=='invalid'; assert code in codes(r); assert r['diagnostics'][0]['repair_target_stage'] in {'/decompose','/architectures'}

def test_stage4_rejects_missing_receipt_reconstruction_bad_candidate_and_unknown_total():
    expected={'T10':'ASB-UPSTREAM-VALIDATION-REQUIRED','T11':'ASB-DOWNSTREAM-RECONSTRUCTION-FORBIDDEN','T12':'ASB-CANDIDATE-NOT-IN-VALIDATED-STAGE3','T16':'ASB-FINAL-TOTAL-WITH-UNKNOWN'}
    v=asb.Validator(ROOT)
    for case,code in expected.items():
        r=v.validate_sequence(ROOT/'fixtures/architect-pipeline-stage-boundary/invalid'/case)
        assert code in codes(r)

def test_anchor_and_stage5_fail_closed():
    v=asb.Validator(ROOT)
    for case,code in {'T14':'ASB-ANCHOR-DIGEST-MISMATCH','T15':'ASB-ANCHOR-VALID-RECEIPT-REQUIRED','T17':'ASB-STAGE5-MISSING-VALID-STAGE4'}.items():
        p=next((ROOT/'fixtures/architect-pipeline-stage-boundary/invalid'/case).glob('*.json'))
        r=v.validate_path(p)
        assert r['status']=='invalid'; assert code in codes(r)

def test_incident_regression_fails_at_earliest_stage2_boundary():
    r=asb.Validator(ROOT).validate_sequence(ROOT/'fixtures/architect-pipeline-stage-boundary/invalid/incident-fail-late')
    assert r['status']=='invalid'; assert r['diagnostics'][0]['stage_id']=='/decompose'; assert r['diagnostics'][0]['rule_id']=='ASB-R01'

def test_receipt_digest_changes_with_exact_bytes_and_cli_writes_receipt(tmp_path):
    src=ROOT/'fixtures/architect-pipeline-stage-boundary/valid/decompose.valid.json'
    a=tmp_path/'a.json'; b=tmp_path/'b.json'; a.write_bytes(src.read_bytes()); b.write_bytes(src.read_bytes()+b'\n')
    ra=json.loads(run('--artifact',str(a),'--format','json').stdout); rb=json.loads(run('--artifact',str(b),'--format','json').stdout)
    assert ra['artifact_sha256']!=rb['artifact_sha256']
    out=tmp_path/'receipt.json'; cp=run('--artifact',str(a),'--write-receipt',str(out)); assert cp.returncode==0; assert json.loads(out.read_text())['status']=='valid'

def test_fixture_cli_and_json_sequence_output():
    assert run('--fixtures').returncode==0
    cp=run('--sequence','fixtures/architect-pipeline-stage-boundary/valid/complete-sequence','--format','json')
    assert cp.returncode==0; assert json.loads(cp.stdout)['status']=='valid'

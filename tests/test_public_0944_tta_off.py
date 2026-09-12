"""Exercise the new execution gate and final-graph serialization boundary."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import pytest
from scripts.build_public_0944_tta_off import EXPORT_HELPER, TARGET, build
from scripts.validate_public_0944_tta_off import validate

def runtime(tmp_path):
    ns={'json':json,'WORKING_DIR':tmp_path,'_sha256_file':lambda p:hashlib.sha256(p.read_bytes()).hexdigest()}
    exec(EXPORT_HELPER,ns)
    return ns

def test_frozen_boundaries():
    assert validate(TARGET)['passed']

@pytest.mark.parametrize('receipts,expected', [
    ([],False),
    ([{'phase':'test','enabled':False,'views':8}],False),
    ([{'phase':'test','enabled':True,'views':8},{'phase':'validation','enabled':False,'views':8}],False),
    ([{'phase':'test','enabled':False,'views':7},{'phase':'validation','enabled':False,'views':8}],False),
    ([{'phase':'test','enabled':False,'views':8},{'phase':'validation','enabled':False,'views':8}],True),
])
def test_executed_branch_gate(tmp_path,receipts,expected):
    assert runtime(tmp_path)['valid_tta_off_receipts'](receipts) is expected

def test_final_graph_roundtrip_preserves_inputs(tmp_path):
    ns=runtime(tmp_path)
    nodes={5:(0,1.25,2.5,3.75),8:(1,2.,3.,4.)}; edges=[(5,8)]
    old=copy.deepcopy((nodes,edges))
    r=ns['export_scored_graph']('example',nodes,edges,nodes,edges,2.,{'t_pred':2})
    payload=json.loads(gzip.decompress(Path(r['path']).read_bytes()))
    assert payload['pred_nodes']==[[5,0,1.25,2.5,3.75],[8,1,2.,3.,4.]]
    assert payload['pred_edges']==[[5,8]] and payload['graph_stage']=='final_scored_after_linefit'
    assert (nodes,edges)==old
    assert r['nodes']==2 and r['edges']==1

def test_nonfinite_graph_rejected(tmp_path):
    ns=runtime(tmp_path)
    with pytest.raises(ValueError):
        ns['export_scored_graph']('bad',{1:(0,float('nan'),1.,2.)},[],{},[],1.,{})
    assert not (tmp_path/'final_validation_graphs').exists()

def test_snapshot_tamper_rejected(tmp_path):
    nb=build();nb['cells'][2]['source']=[s.replace("os.environ['BIOHUB_EDGE_FEATURE_TTA'] = '0'","os.environ['BIOHUB_EDGE_FEATURE_TTA'] = '1'") for s in nb['cells'][2]['source']]
    p=tmp_path/'tampered.ipynb';p.write_text(json.dumps(nb))
    with pytest.raises(AssertionError,match='deterministic'):
        validate(p)

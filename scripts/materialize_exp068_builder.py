"""Create the isolated builder without editing historical exp066 implementation."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'scripts/build_exp066_probe.py').read_text(encoding='utf-8')
source = source.replace('exp_066', 'exp_068').replace('exp066', 'exp068')
source = source.replace('out_dir = ROOT / f"experiments/exp_068_probe_{arm}/kaggle_kernel"', 'out_dir = ROOT / "scratchpad/exp068_build"')
source = source.replace('    overrides = ARMS[arm]', '    assert arm == "ep015", "Only the authorized ep015 arm is allowed"\n    overrides = ARMS[arm]')
anchor = '    out_dir = ROOT / "scratchpad/exp068_build"'
assert source.count(anchor) == 1
source = source.replace(anchor, '    from exp068_build_support import add_contract, write_config\n    nb = add_contract(nb)\n    write_config()\n' + anchor)
path = ROOT / 'scripts/build_exp068_probe.py'
assert not path.exists(), 'Do not overwrite an existing builder'
path.write_text(source, encoding='utf-8')
print(path)

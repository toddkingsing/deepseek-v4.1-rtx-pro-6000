"""Only for this task's pinned Moet candidate image; no kernel arithmetic changes."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import sysconfig

assert os.environ.get('DEEPSEEK_SPEED2_CANDIDATE_BUILD') == '1', 'Run only in the candidate Docker build'
assert importlib.metadata.version('flashinfer-python') == '0.7.2'
site = Path(sysconfig.get_paths()['purelib'])
path = site/'flashinfer/experimental/b12x/moe/fused_moe/_impl.py'
host = site/'flashinfer/experimental/b12x/moe/_shared/kernels/w4a16/host.py'
old = path.read_text()
assert hashlib.sha256(path.read_bytes()).hexdigest() == '16af55b31d09ef8a5017cd4a7357ce5a525a9963851cf92794030e735450f082'
assert hashlib.sha256(host.read_bytes()).hexdigest() == '1766d852a76711c3c80fefd982e4b6586f2c89d769310225d7bbf371e8c3d8ea'
assert 'cache2_width = ((intermediate_size + 255) // 256) * 256' in host.read_text()
anchor = '        intermediate_cache2_elements = routed_capacity * int(n)\n'
replacement = '''        # Reserve the aligned modelopt W4A16 micro-decode scratch width.
        # A frozen plan may execute fewer live tokens than its capacity.
        # Match host.plan_w4a16_buffers; keep kernel checks and math unchanged.
        cache2_width = int(n)
        if weight_layout == "modelopt" and not full_rotation:
            cache2_width = ((cache2_width + 255) // 256) * 256
        intermediate_cache2_elements = routed_capacity * cache2_width
'''
assert old.count(anchor) == 1
new = old.replace(anchor, replacement, 1)
compile(new, str(path), 'exec')
out = Path('/opt/deepseek-speed2')
out.mkdir(exist_ok=True)
shutil.copy2(path, out/'flashinfer-impl-before.py')
path.write_text(new)
record = {
    'flashinfer_version': '0.7.2',
    'purpose': 'Reserve aligned W4A16 scratch capacity; no weights, activation dtype or kernel arithmetic changes',
    'path': str(path),
    'before_sha256': hashlib.sha256(old.encode()).hexdigest(),
    'after_sha256': hashlib.sha256(new.encode()).hexdigest(),
    'host_sha256': hashlib.sha256(host.read_bytes()).hexdigest(),
    'original_error': 'intermediate_cache2 has 6912 elements; need at least 9216',
}
(out/'scratch-patch.json').write_text(json.dumps(record, indent=2)+'\n')
print(json.dumps(record))

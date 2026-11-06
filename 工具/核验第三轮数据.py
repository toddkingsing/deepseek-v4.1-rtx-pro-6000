"""Recompute the published third-round figures offline. No network or inference."""
from pathlib import Path
import json,math,statistics
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'数据/2026-11-06-第三轮实测.json').read_text(encoding='utf-8'))
def close(x,y):assert math.isclose(x,y,rel_tol=1e-9,abs_tol=1e-8),(x,y)
assert len(d['trials'])==11
requests=0;hashes=set()
for t in d['trials']:
 assert t['stage']=='complete';batches=t['speed_batches'];assert len(batches)==33;hashes.add(t['prompt_sha256'])
 for b in batches:
  assert b['metrics_delta']['request_success_total']==b['concurrency']
  assert b['metrics_delta']['num_preemptions_total']==0
  requests+=len(b['responses'])
  close(sum(r['usage']['completion_tokens'] for r in b['responses'])/b['wall_s'],b['aggregate_tps'])
  for r in b['responses']:close((r['usage']['completion_tokens']-1)/r['decode_wall_s'],r['decode_tokens_per_s'])
 for s in t['speed_summary']:
  group=[b for b in batches if b['concurrency']==s['c'] and b['case']==s['case']]
  assert len(group)==(5 if s['c']==1 else 3)
  close(statistics.median(r['decode_tokens_per_s'] for b in group for r in b['responses']),s['median_decode_tps'])
  close(statistics.median(b['aggregate_tps'] for b in group),s['median_aggregate_tps'])
 for name in ['cold','interference']:
  for r in t.get(name,[]):assert r['passed'] and r['cold_prefix_hits']==0
 for q in t['quality'].values():assert q['correct']==sum(x['passed'] for x in q['tests']) and q['total']==len(q['tests'])
assert requests==d['speed_requests']==1353 and len(hashes)==1
by={t['variant']:t for t in d['trials']}
for v in ['fused-a8-k3','fused-a8-k5']:
 assert by[v]['quality']['gsm-chat']['correct']==197
 assert [x['id'] for x in by[v]['quality']['gsm-chat']['tests'] if not x['passed']]==[x['id'] for x in by['baseline']['quality']['gsm-chat']['tests'] if not x['passed']]
profiles=json.loads((R/'配置/第三轮W4A8配置.json').read_text(encoding='utf-8'))
for name,k in [('fused-a8-k3',3),('fused-a8-k5',5)]:
 p=profiles[name];a=p['api_server_arguments'];assert p['environment']['VLLM_B12X_MOE_FP4_FORCE_A16']=='0'
 assert json.loads(a[a.index('--speculative-config')+1])['num_speculative_tokens']==k
 assert a[a.index('--max-num-batched-tokens')+1]=='8192'
assert d['deployment']['promoted'] and d['deployment']['profile']=='fused-a8-k5'
print('Third-round evidence verified: 11 records, 1353 speed requests, scores, medians and both profiles.')

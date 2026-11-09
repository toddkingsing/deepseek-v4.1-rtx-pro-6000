from pathlib import Path
import json,math,statistics
G=Path(__file__).resolve().parents[1]
d=json.loads((G/'数据/2026-11-09-eight-gpu.json').read_text(encoding='utf-8'))
def close(a,b):assert math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-7),(a,b)
for label,q in d['speed_batches'].items():
 for b in q['tests']:
  close(b['aggregate_tps'],sum(r['usage']['completion_tokens'] for r in b['responses'])/b['wall_s'])
  for r in b['responses']:close(r['decode_tokens_per_s'],(r['usage']['completion_tokens']-1)/r['decode_wall_s'])
 for s in q['summary']:
  batches=[b for b in q['tests'] if b['concurrency']==s['c'] and b['case']==s['case']]
  close(s['median_aggregate_tps'],statistics.median(b['aggregate_tps'] for b in batches))
  close(s['median_decode_tps'],statistics.median(r['decode_tokens_per_s'] for b in batches for r in b['responses']))
for x in d['same_fixture_comparison']:
 for label in ['original_four','rewired_four']:
  old=next(s for s in d['speed_batches'][label]['summary'] if s['c']==x['concurrency'] and s['case']==x['case'])
  new=next(s for s in d['speed_batches']['final_eight']['summary'] if s['c']==x['concurrency'] and s['case']==x['case'])
  close(x[label],old[x['metric']]);close(x['final'],new[x['metric']]);close(x['ratio_to_'+label],x['final']/x[label])
for x in d['capacity']:
 assert x['passed'] and x['cleanup_complete'] and x['simultaneous_hold_seconds']>=60 and x['cold_prefix_hits']==0
 assert len(x['requests'])==x['concurrency'] and all(r['retrieval_passed'] and r['usage']['prompt_tokens']>=1000000 for r in x['requests'])
 rates=[(b-a)/x['simultaneous_hold_seconds'] for a,b in zip(x['hold_start_completion_tokens'],x['hold_end_completion_tokens'],strict=True)]
 for a,b in zip(rates,x['per_stream_decode_tps'],strict=True):close(a,b)
 close(sum(rates),x['aggregate_decode_tps'])
 waits=[r['first_token_s']-r['submitted_s'] for r in x['requests']]
 close(statistics.median(waits),x['cold_ttft_median']);close(max(waits),x['cold_ttft_max'])
a=d['gsm_scored_answers']['original_four'];b=d['gsm_scored_answers']['final_eight']
assert a['selection_sha256']==b['selection_sha256'] and a['total']==b['total']==200
for q in [a,b]:assert sum(x['passed'] for x in q['tests'])==q['correct']==197
assert all(x['id']==y['id'] and x['expected']==y['expected'] and x['actual']==y['actual'] for x,y in zip(a['tests'],b['tests'],strict=True))
assert d['soak']=={'status':'cancelled_by_user','performed':False}
print('PASS: three speed datasets, nine comparisons, C10/C24 simultaneous rates and cold TTFT, paired GSM scores, and cancelled-soak status. Offline only; no inference or network calls.')

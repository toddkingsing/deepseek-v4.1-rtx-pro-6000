"""Validate the published evidence internally; no network or model requests."""
from pathlib import Path
import csv
import json
import math
import statistics

ROOT = Path(__file__).resolve().parents[1]

def read(name):
    return json.loads((ROOT / '数据' / name).read_text(encoding='utf-8-sig'))

def close(actual, expected):
    if not math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-8):
        raise ValueError(f'Mismatch: {actual} != {expected}')

summary = read('对照汇总.json')
scores = read('逐题评分.json')
speed = read('短输入逐轮计时.json')
for model in ('official', 'abliterated'):
    for case, group in scores[model].items():
        correct = sum(row['passed'] for row in group['tests'])
        assert correct == group['correct'] == summary['quality'][case][model+'_correct']
        assert len(group['tests']) == group['total'] == summary['quality'][case]['total']
    assert len(speed[model]) == 9
    for case in ('chinese', 'code', 'english'):
        rows = [r for r in speed[model] if r['case'] == case]
        assert len(rows) == 3
        for row in rows:
            assert row['usage']['completion_tokens'] == 1024
            close((row['usage']['completion_tokens']-1)/row['decode_wall_s'], row['decode_tokens_per_s'])
        close(statistics.median(r['decode_tokens_per_s'] for r in rows), summary['speed'][case][model+'_median_tps'])
    long = summary['long_context'][model]
    assert long['passed'] and long['usage']['prompt_tokens'] == 999906
    assert long['usage']['completion_tokens'] == 1024
    assert all(x['passed'] for x in summary['application'][model]['checks'])
    with (ROOT / '数据' / f'{model}-百万输入资源采样.csv').open(encoding='utf-8-sig', newline='') as f:
        telemetry = list(csv.DictReader(f))
    peaks = summary['resource_peaks'][model]
    for gpu in range(4):
        rows = [r for r in telemetry if int(r['gpu']) == gpu]
        close(max(float(r['memory_MiB']) for r in rows)/1024, peaks['gpu_memory_GiB'][str(gpu)])
        close(max(float(r['power_W']) for r in rows), peaks['gpu_power_W'][str(gpu)])
    for col, key in [('host_total_minus_available_GiB','host_total_minus_available_GiB'),('cgroup_memory_GiB','cgroup_including_file_cache_GiB')]:
        assert abs(max(float(r[col]) for r in telemetry)-peaks[key]) < 0.0001
    assert all(int(r['cgroup_swap_bytes']) == 0 for r in telemetry)
    print(model, 'quality and timing checks passed')
for case, row in summary['speed'].items():
    close((row['abliterated_median_tps']/row['official_median_tps']-1)*100, row['change_percent'])
print('All published score and timing consistency checks passed.')

#!/usr/bin/env python3
import json
from collections import defaultdict
from pathlib import Path

def analyze_file(path):
    with open(path, encoding='utf-8') as f:
        records = [json.loads(line) for line in f if line.strip()]
    ok = [r for r in records if not r.get('error')]
    
    # Overall
    overall = sum(r['final']['total'] for r in ok) / len(ok) if ok else 0
    
    # Modes
    by_mode = defaultdict(list)
    for r in ok:
        by_mode[r['mode']].append(r['final']['total'])
    mode_avg = {m: sum(lst)/len(lst) for m, lst in by_mode.items()}
    
    # Domains
    by_domain = defaultdict(list)
    for r in ok:
        by_domain[r.get('domain', 'unknown')].append(r['final']['total'])
    domain_avg = {d: sum(lst)/len(lst) for d, lst in by_domain.items()}
    
    # Task Types
    by_tt = defaultdict(list)
    for r in ok:
        by_tt[r.get('task_type', 'unknown')].append(r['final']['total'])
    tt_avg = {t: sum(lst)/len(lst) for t, lst in by_tt.items()}
    
    return {
        'total_count': len(records),
        'ok_count': len(ok),
        'overall': overall,
        'modes': mode_avg,
        'domains': domain_avg,
        'task_types': tt_avg
    }

def main():
    models = {
        'Claude-Sonnet-4.6 (GPT-5.5 Judge)': 'outputs/m4r1/claude-sonnet-4-6_regraded_gpt_judge.jsonl',
        'GPT-5.5 (GPT-5.5 Judge)': 'outputs/m4r1/gpt-5.5_regraded_gpt_judge.jsonl',
        'Gemini-2.5-Flash (GPT-5.5 Judge)': 'outputs/m4r1/gemini-2.5-flash_20260613T140934Z.jsonl'
    }

    for name, path in models.items():
        if not Path(path).exists():
            print(f"File not found: {path}")
            continue
        stats = analyze_file(path)
        print(f'=== {name} ===')
        print(f"Runs: {stats['ok_count']}/{stats['total_count']}")
        print(f"Overall Score: {stats['overall']:.2f}")
        print('Modes:')
        for m, val in stats['modes'].items():
            print(f"  {m}: {val:.2f}")
        print('Domains:')
        for d, val in sorted(stats['domains'].items()):
            print(f"  {d}: {val:.2f}")
        print('Task Types:')
        for t, val in sorted(stats['task_types'].items()):
            print(f"  {t}: {val:.2f}")
        print()

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Offline structure and reference-integrity checks; NOT online fact checking."""
import json, re, sys
from pathlib import Path

def validate(data):
    errors=[]
    if not isinstance(data,dict): return ['Root must be an object']
    for k in ('question','search_log','papers','candidates'):
        if k not in data: errors.append(f'Missing {k}')
    if not isinstance(data.get('question'),str) or len(data.get('question','').strip())<5: errors.append('question must be descriptive')
    for k in ('search_log','papers','candidates'):
        if not isinstance(data.get(k),list): errors.append(f'{k} must be a list')
    ids=set()
    for i,p in enumerate(data.get('papers',[]) if isinstance(data.get('papers'),list) else []):
        if not isinstance(p,dict): errors.append(f'papers[{i}] must be an object'); continue
        for k in ('id','title','source_type','access_level','verification_status'):
            if not isinstance(p.get(k),str) or not p[k].strip(): errors.append(f'papers[{i}].{k} missing')
        if p.get('id') in ids: errors.append(f'duplicate paper id {p.get("id")}')
        ids.add(p.get('id'))
        if p.get('source_type') not in ('uploaded','retrieved'): errors.append(f'papers[{i}] invalid source_type')
        if p.get('access_level') not in ('full_text','abstract','metadata','uploaded_full_text'): errors.append(f'papers[{i}] invalid access_level')
        if p.get('verification_status') not in ('verified','unverified','not_applicable'): errors.append(f'papers[{i}] invalid verification_status')
        if 'pmid' in p and not re.fullmatch(r'[0-9]+',str(p['pmid'])): errors.append(f'papers[{i}] invalid PMID syntax')
        if 'doi' in p and not re.match(r'^10\.\d{4,9}/\S+$',str(p['doi']),re.I): errors.append(f'papers[{i}] invalid DOI syntax')
    for i,c in enumerate(data.get('candidates',[]) if isinstance(data.get('candidates'),list) else []):
        if not isinstance(c,dict): errors.append(f'candidates[{i}] must be an object'); continue
        for k in ('variable','role','rationale','recommendation'):
            if not isinstance(c.get(k),str) or not c[k].strip(): errors.append(f'candidates[{i}].{k} missing')
        if c.get('role') not in ('candidate confounder','possible mediator','possible collider/selection variable','precision variable','uncertain','not recommended for primary adjustment'): errors.append(f'candidates[{i}] invalid role')
        if not isinstance(c.get('paper_ids'),list): errors.append(f'candidates[{i}].paper_ids must be a list')
        else:
            for ref in c['paper_ids']:
                if ref not in ids: errors.append(f'candidates[{i}] references unknown paper {ref}')
    for i,q in enumerate(data.get('search_log',[]) if isinstance(data.get('search_log'),list) else []):
        if not isinstance(q,dict) or not all(isinstance(q.get(k),str) and q[k].strip() for k in ('source','query','date')): errors.append(f'search_log[{i}] incomplete')
    return errors

def main():
    if len(sys.argv)!=2: print('Usage: validate_evidence.py ledger.json',file=sys.stderr);return 2
    try: data=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    except (OSError,ValueError) as e: print(f'Could not read JSON: {e}',file=sys.stderr);return 2
    errors=validate(data)
    if errors:
        for e in errors: print('ERROR:',e,file=sys.stderr)
        return 1
    print('PASS: structural checks passed; external citation verification still required.')
    return 0
if __name__=='__main__': raise SystemExit(main())

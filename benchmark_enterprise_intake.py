"""Measured extraction / retrieval benchmark, NOT model accuracy or an ISO audit."""
import argparse
import hashlib
import json
import time
import tracemalloc
from pathlib import Path
from tempfile import TemporaryDirectory
from evidence_collectors.document_parser import extract_document_text


def benchmark(count):
    if not 1<=count<=1000:raise ValueError('1–1000 files')
    with TemporaryDirectory(prefix='iso-intake-benchmark-') as temp:
        root=Path(temp)
        for n in range(count):
            # Deliberate duplicates, malformed binary, unsupported extension, and stale/conflicting claims.
            extension='.bin' if n%31==0 else '.txt'
            payload=(f'SYNTHETIC enterprise {n%3} period 2024-{n%12+1:02d}. Asset {n%97}. '
                     'Backup completed; restore verification absent. Conflicting endpoint reports require owner review. '
                     'This fixture is not an expert assessment or compliance conclusion. ')
            raw=b'\x00\xffbroken' if n%29==0 else payload.encode()
            if n%10==0 and n>0:raw=(root/f'{n-1}.txt').read_bytes() if (root/f'{n-1}.txt').exists() else raw
            (root/f'{n}{extension}').write_bytes(raw)
        seen=set();results=[];index={};tracemalloc.start();start=time.perf_counter();cpu=time.process_time()
        for path in sorted(root.iterdir()):
            raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
            try:
                if path.suffix!='.txt':raise ValueError('Unsupported extension')
                if digest in seen:results.append(dict(file=path.name,status='duplicate',sha256=digest));continue
                seen.add(digest);text=raw.decode('utf-8-sig')
                if '\x00' in text:raise ValueError('Binary text')
                from evidence_collectors.source_quality import text_quality
                if not text_quality(text)['usable']:raise ValueError('Unusable text')
                for token in set(text.lower().split()):index.setdefault(token,set()).add(path.name)
                results.append(dict(file=path.name,status='extracted',sha256=digest,characters=len(text)))
            except (ValueError,UnicodeError) as exc:results.append(dict(file=path.name,status='rejected',error=type(exc).__name__))
        query_start=time.perf_counter();hits=sorted(index.get('backup',set()));query_seconds=time.perf_counter()-query_start
        elapsed=time.perf_counter()-start;cpu_seconds=time.process_time()-cpu;_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        return dict(protocol='enterprise-intake-benchmark-v1',synthetic=True,files=count,processed=len(results),
            counts={state:sum(r['status']==state for r in results) for state in ('extracted','duplicate','rejected')},
            wall_seconds=elapsed,cpu_seconds=cpu_seconds,python_peak_allocated_bytes=peak,
            memory_note='tracemalloc Python allocations, not total process RSS',search_seconds=query_seconds,search_hits=len(hits),
            model_calls=0,independent_accuracy=None,results=results,
            limitations='Extraction/lexical index only. Does not measure PDF OCR, vector retrieval, aggregate LLM reasoning or production concurrency.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--counts',default='10,100,500,1000');parser.add_argument('--output',required=True);args=parser.parse_args()
    path=Path(args.output)
    if path.exists():raise SystemExit('Output exists; preserve prior benchmark')
    reports=[benchmark(int(n)) for n in args.counts.split(',')];path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(dict(reports=reports),indent=2),encoding='utf-8')
    print(json.dumps([dict(files=r['files'],counts=r['counts'],seconds=r['wall_seconds'],peak_bytes=r['python_peak_allocated_bytes']) for r in reports]))

"""Bridge natural_reference records to descriptive acoustics, with no new scores."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from acoustic_analysis import analyze,sha256,write_outputs
import soundfile as sf


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest',type=Path)
    parser.add_argument('--output-dir',required=True,type=Path)
    parser.add_argument('--limit',type=int,default=1)
    parser.add_argument('--run',action='store_true',help='Without this flag only print planned jobs')
    args=parser.parse_args()
    if args.limit<1:parser.error('limit must be positive')
    records=[json.loads(line) for line in args.manifest.read_text(encoding='utf-8').splitlines() if line.strip()]
    for record in records[:args.limit]:
        if record.get('sample_type')!='natural_reference':raise ValueError('Natural references only')
        if record['natural_source']['license']['status']!='verified_for_planned_use':raise ValueError('License not verified')
        path=ROOT/record['audio']['path']
        if sha256(path)!=record['audio']['sha256']:raise ValueError('Source hash mismatch')
        info=sf.info(path);window=2*round((2048/24000)*info.samplerate/2)
        destination=args.output_dir/record['example_id'].replace(':','_')
        job={'example_id':record['example_id'],'source':str(path),'output_dir':str(destination),'frame_length':window,'hop_ms':10,'fmin':65,'fmax':500,'operation':'descriptive_only','normalization':'utterance median provisional; not corpus speaker normalization'}
        print(json.dumps(job))
        if args.run:
            report,frames=analyze(path,frame_length=window)
            report['example_id']=record['example_id'];report['sample_type']='natural_reference'
            write_outputs(report,frames,destination)


if __name__=='__main__':main()

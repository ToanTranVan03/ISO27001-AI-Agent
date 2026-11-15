"""Export existing evidence-bound A.8 reports without fabricating human ratings."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from agent_core.a8_teacher_pipeline import load_reports,build_assessor_ground_truth,export_all_deliverables


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reports',nargs='+',required=True)
    parser.add_argument('--labels',help='Actual submitted reviewer-label list, with report/evidence hashes')
    parser.add_argument('--output-dir',required=True,help='New output directory; existing results are never overwritten')
    args=parser.parse_args()
    try:
        result=export_all_deliverables(load_reports(args.reports),args.output_dir,
            build_assessor_ground_truth(args.labels) if args.labels else [])
    except (ValueError,OSError,KeyError,TypeError) as exc:parser.exit(1,f'Cannot export: {exc}\n')
    print(f"Exported {len(result['input_report_hashes'])} reports to {args.output_dir}; SoA remains draft.")


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8')
    main()

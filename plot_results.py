import argparse
import csv
import json
from pathlib import Path
import matplotlib.pyplot as plt

def read_histogram_csv(path):
    xs, ys = [], []
    with open(path, 'r', newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or row[0].startswith('#'):
                continue
            if len(row) < 2:
                continue
            try:
                x = int(row[0])
                y = float(row[1])
            except ValueError:
                continue
            xs.append(x)
            ys.append(y)
    return xs, ys

def read_metrics(path):
    p = Path(path)
    if p.suffix.lower() == '.json':
        with open(p, 'r') as f:
            data = json.load(f)
        return float(data.get('avg_req_dist'))
    else:
        # csv: look for header and column
        with open(p, 'r', newline='') as f:
            reader = csv.DictReader(f)
            avg = None
            for row in reader:
                if 'avg_req_dist' in row:
                    avg = float(row['avg_req_dist'])
                    break
        if avg is None:
            raise ValueError(f"No 'avg_req_dist' in {path}")
        return avg

def main():
    ap = argparse.ArgumentParser(description="Plot queue-length histograms and request distances.")
    ap.add_argument('--hist', nargs='+', required=True,
                    help="One or more entries of the form path[:label] for histogram CSVs.")
    ap.add_argument('--metrics', nargs='*',
                    help="Optional entries of the form path[:label] for metrics (JSON or CSV with avg_req_dist).")
    ap.add_argument('--xmax', type=int, default=10, help='Max x (queue length) to show.')
    ap.add_argument('--outdir', default='plots', help='Output directory.')
    ap.add_argument('--title', default='', help='Optional plot title suffix.')
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # Load and plot histograms
    plt.figure()
    for spec in args.hist:
        if ':' in spec:
            path, label = spec.split(':', 1)
        else:
            path, label = spec, Path(spec).stem
        xs, ys = read_histogram_csv(path)
        # limit to xmax
        xs2, ys2 = [], []
        for x, y in zip(xs, ys):
            if x <= args.xmax:
                xs2.append(x)
                ys2.append(y)
        plt.plot(xs2, ys2, label=label)
    plt.xlim(0, args.xmax)
    plt.grid(True)
    plt.xlabel('Queue Length')
    plt.ylabel('Load distribution (P{len = x})')
    if args.title:
        plt.title(f'Load Distribution - {args.title}')
    else:
        plt.title('Load Distribution')
    plt.legend()
    ld_path = outdir / 'load_distribution.png'
    plt.savefig(ld_path, bbox_inches='tight')
    # Do not show, as this is a script.
    plt.close()

    # Optionally plot request distance bars
    if args.metrics:
        labels = []
        values = []
        for spec in args.metrics:
            if ':' in spec:
                path, label = spec.split(':', 1)
            else:
                path, label = spec, Path(spec).stem
            labels.append(label)
            values.append(read_metrics(path))

        plt.figure()
        plt.bar(labels, values)
        plt.xlabel('Algorithm')
        plt.ylabel('Average request distance')
        if args.title:
            plt.title(f'Request Distance - {args.title}')
        else:
            plt.title('Request Distance')
        rd_path = outdir / 'request_distance.png'
        plt.savefig(rd_path, bbox_inches='tight')
        plt.close()

    print(f"Saved: {ld_path}")
    if args.metrics:
        print(f"Saved: {rd_path}")

if __name__ == '__main__':
    main()

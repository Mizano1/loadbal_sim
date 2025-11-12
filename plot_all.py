import json, csv
import matplotlib.pyplot as plt
from pathlib import Path

PLOTS = Path("plots")
PLOTS.mkdir(exist_ok=True)

# Discover all *_hist.csv and *_metrics.json
hist_files = sorted(PLOTS.glob("*_hist.csv"))
metric_files = sorted(PLOTS.glob("*_metrics.json"))

if not hist_files:
    print("No *_hist.csv files found in 'plots/'. Run your simulator first.")
    raise SystemExit(1)

# Load histograms
hist = {}
for f in hist_files:
    policy = f.stem.replace("_hist", "")
    xs, ys = [], []
    with open(f) as fin:
        for row in csv.reader(fin):
            if len(row) < 2 or (row and str(row[0]).startswith('#')):
                continue
            try:
                xs.append(int(row[0]))
                ys.append(float(row[1]))
            except Exception:
                pass
    hist[policy] = (xs, ys)

# Plot load distributions
plt.figure()
for policy, (xs, ys) in hist.items():
    plt.plot(xs, ys, label=policy)
plt.xlim(0, 10)
plt.xlabel("Queue length")
plt.ylabel("Probability")
plt.title("Load Distribution Comparison")
plt.grid(True)
plt.legend()
plt.savefig(PLOTS / "load_distribution.png", bbox_inches="tight")
print("Saved plots/load_distribution.png")

# Plot average request distances (if available)
metrics = {}
for f in metric_files:
    policy = f.stem.replace("_metrics", "")
    try:
        data = json.load(open(f))
        metrics[policy] = float(data.get("avg_req_dist", 0.0))
    except Exception:
        pass

if metrics:
    plt.figure()
    labels = list(metrics.keys())
    vals = [metrics[k] for k in labels]
    plt.bar(labels, vals)
    plt.ylabel("Average request distance")
    plt.title("Request Distance Comparison")
    plt.grid(True, axis="y")
    plt.savefig(PLOTS / "request_distance.png", bbox_inches="tight")
    print("Saved plots/request_distance.png")
else:
    print("No *_metrics.json files found; skipping request-distance plot.")

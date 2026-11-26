import json
import os
import matplotlib.pyplot as plt
import numpy as np

# ------------------------------
# Step 1: Load JSON files
# ------------------------------
folder = "data"

files = {
    "lambda_5_logs": "lambda_5_random.json",
    "lambda_10_logs": "lambda_10_random.json",
    "lambda_5d_logs": "lambda_5_biased.json",
    "lambda_10d_logs": "lambda_10_biased.json"
}

logs_dict = {}

for key, filename in files.items():
    path = os.path.join(folder, filename)
    with open(path, "r") as f:
        logs_dict[key] = json.load(f)

print("Datasets loaded:", logs_dict.keys())


scheduler_name_map = {
    "BruteForce": "Resource-Prioritize",
    "EPRNew": "EPR (Node Selection)",
    "PPONew": "PPO (Node Selection)",
    "List": "LIST",
}

# ------------------------------
# Step 2: Plotting function
# ------------------------------
def plot_cdf_comparison(logs, metric_key, x_label_name, metric_name=None, save_pattern="cdf"):
    plt.figure(figsize=(6, 4))
    metric_name = metric_name or metric_key

    markers = ['o', 's', 'D', '^', 'v', '*', 'x', 'P', 'h']
    colors = ['b', 'y', 'r', 'c', 'm', 'g', 'k', 'orange', 'purple']

    for i, (scheduler_name, data) in enumerate(logs.items()):

        label_name = scheduler_name_map.get(scheduler_name, scheduler_name)

        metric_values = np.array([v for v in data.get(metric_key, []) if v is not None])
        if len(metric_values) == 0:
            continue

        if metric_key == "Makespan":
            metric_values = metric_values / 1e9  # ns -> s

        sorted_vals = np.sort(metric_values)
        cdf = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)

        if scheduler_name == "PPONew":
            line_style = "--"
        else:
            line_style = "-"

        plt.plot(
            sorted_vals,
            cdf,
            label=label_name,
            linewidth=2,
            linestyle=line_style,
            color=colors[i % len(colors)],
            marker=markers[i % len(markers)],
            markersize=6,
            markevery=max(len(sorted_vals)//10, 1)
        )

    plt.xlabel(x_label_name, fontsize=16)
    plt.ylabel("Cumulative Probability", fontsize=16)
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)
    plt.grid(True, linestyle="--", alpha=0.6)
    if save_pattern == 'cdf':
        plt.legend()
    plt.tight_layout()

    filename = f"{save_pattern}_{metric_name.replace(' ', '_').lower()}.pdf"

    plt.savefig(filename, bbox_inches="tight")
    plt.close()

    print(f"Saved plot: {filename}")


# ------------------------------
# Step 3: Define datasets
# ------------------------------
plot_groups = [
    {"logs_pattern": "lambda_5_logs", "save_pattern": "cdf"},
    {"logs_pattern": "lambda_5d_logs", "save_pattern": "cdf_5_dist"},
    {"logs_pattern": "lambda_10_logs", "save_pattern": "cdf_10"},
    {"logs_pattern": "lambda_10d_logs", "save_pattern": "cdf_10_dist"},
]

metrics_to_plot = [
    {"metric": "Makespan", "x_label": "Makespan (s)", "metric_name": None},
    {"metric": "SNP", "x_label": "SELP", "metric_name": "SELP"},
    {"metric": "Fairness", "x_label": "Fairness", "metric_name": None},
    {"metric": "QPU Utilization", "x_label": "QPU Utilization", "metric_name": None},
    {"metric": "Network Utilization", "x_label": "Non-local gate rate", "metric_name": "Non-local gate rate"},
]


# ------------------------------
# Step 4: Generate plots
# ------------------------------
for group in plot_groups:
    logs = logs_dict.get(group["logs_pattern"])

    if logs is None:
        print("Missing dataset:", group["logs_pattern"])
        continue

    for cfg in metrics_to_plot:
        plot_cdf_comparison(
            logs,
            metric_key=cfg["metric"],
            x_label_name=cfg["x_label"],
            metric_name=cfg["metric_name"],
            save_pattern=group["save_pattern"]
        )

# ------------------------------
# Step 5: Calculate mean and std
# ------------------------------

for dataset_name, dataset in logs_dict.items():
    print(f"\n=== {dataset_name} ===")

    for scheduler, data in dataset.items():
        print(f"\n{scheduler_name_map.get(scheduler, scheduler)}")

        for metric, values in data.items():
            vals = np.array([v for v in values if v is not None])

            if len(vals) == 0:
                continue

            if metric == "Makespan":
                mean = np.mean(vals) / 1e9  # ns -> s
                std = np.std(vals, ddof=1) / 1e9
                unit = "s"
            else:
                mean = np.mean(vals)
                std = np.std(vals, ddof=1)
                unit = ""

            print(
                f"{metric:20s} "
                f"mean={mean:.4f} {unit} "
                f"std={std:.4f} {unit}"
            )
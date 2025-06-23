import argparse
import re
from pathlib import Path


def parse_benchmark_line(line: str):
    """
    Parses a single line of benchmark output.

    Example line:
    MUL_MAT(...): 744 runs - 1660.11 us/run - 134.48 MFLOP/run - 81.01 GFLOPS

    Returns a tuple of (key, gflops) or (None, None) if parsing fails.
    """
    line = line.strip()
    if ':' not in line:
        return None, None

    key, data_part = line.split(':', 1)
    key = key.strip()

    # Find the last number and unit in the data part
    match = re.search(r'([\d\.]+)\s+(GFLOPS|TFLOPS|MFLOPS)$', data_part.strip())
    if not match:
        return None, None

    value_str, unit = match.groups()
    value = float(value_str)

    # Normalize everything to GFLOPS
    if unit == 'TFLOPS':
        gflops = value * 1000
    elif unit == 'MFLOPS':
        gflops = value / 1000
    else:  # GFLOPS
        gflops = value

    return key, gflops


def load_results(filepath: Path) -> dict:
    """Loads all benchmark results from a file into a dictionary."""
    results = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                key, gflops = parse_benchmark_line(line)
                if key:
                    results[key] = gflops
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        exit(1)
    return results


def format_change(change: float) -> str:
    """Formats the percentage change."""
    if change > 0.1:
        return f"+{change:.2f}%"
    elif change < -0.1:
        return f"{change:.2f}%"
    else:
        return " ~0.00%"


def main():
    """Main function to compare benchmark files."""
    parser = argparse.ArgumentParser(
        description="Compare two benchmark result files and generate a report.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("old_file", type=Path, help="Path to the 'before' benchmark results file.")
    parser.add_argument("new_file", type=Path, help="Path to the 'after' benchmark results file.")
    parser.add_argument(
        "-o", "--output", type=Path, default="comparison_report.txt",
        help="Path to the output report file (default: comparison_report.txt)."
    )
    args = parser.parse_args()

    print(f"Loading old results from: {args.old_file}")
    old_results = load_results(args.old_file)
    print(f"Loading new results from: {args.new_file}")
    new_results = load_results(args.new_file)

    if not old_results or not new_results:
        print("Could not load results from one or both files. Exiting.")
        return

    all_keys = sorted(list(set(old_results.keys()) | set(new_results.keys())))

    comparisons = []

    for key in all_keys:
        old_val = old_results.get(key)
        new_val = new_results.get(key)

        entry = {"key": key, "old": old_val, "new": new_val, "change": 0}

        if old_val is not None and new_val is not None:
            entry["change"] = ((new_val - old_val) / old_val) * 100

        comparisons.append(entry)

    # --- Generate Report ---
    with open(args.output, 'w', encoding='utf-8') as f:

        # Create header
        key_width = max(len(k) for k in all_keys) + 2
        header = f"{'Test Configuration':<{key_width}} {'Old GFLOPS':>15} {'New GFLOPS':>15} {'Change (%)':>15}"
        f.write(header + "\n")
        f.write("-" * len(header) + "\n")

        for item in comparisons:
            old_str = f"{item['old']:.2f}" if item['old'] is not None else "N/A"
            new_str = f"{item['new']:.2f}" if item['new'] is not None else "N/A"
            change_str = format_change(item['change'])
            f.write(f"{item['key']:<95} {old_str:>15} {new_str:>15} {change_str:>15}\n")

    print(f"Comparison report successfully generated at: {args.output}")


if __name__ == "__main__":
    main()

import re
import sys

def split_file(file_path):
    """
    Splits the file into three sections:
      - header: all lines before the first line containing "GB/s"
      - bench: contiguous lines that contain "GB/s"
      - footer: all lines after the bench section
    """
    header = []
    bench = []
    footer = []
    with open(file_path) as f:
        lines = f.readlines()
    
    i = 0
    n = len(lines)
    # Collect header: until we find a line containing "GB/s"
    while i < n and "GB/s" not in lines[i]:
        header.append(lines[i])
        i += 1
    # Collect benchmark lines: all consecutive lines that contain "GB/s"
    while i < n and "GB/s" in lines[i]:
        bench.append(lines[i])
        i += 1
    # The rest is footer
    while i < n:
        footer.append(lines[i])
        i += 1
    return header, bench, footer

def extract_throughput(line):
    """
    Extracts the throughput value and its unit from a benchmark line.
    Returns a tuple (value, unit) if found, or (None, None) if not.
    This function uses regex to find all number/unit pairs and returns the last match.
    """
    matches = re.findall(r'(\d+(?:\.\d+)?)\s+(\S+)', line)
    if matches:
        value, unit = matches[-1]
        try:
            return float(value), unit
        except ValueError:
            return None, None
    return None, None

def extract_test_signature(line):
    """
    Extracts the full test (bench) signature from the beginning of the line,
    i.e. everything up to and including the first occurrence of "):".
    Returns None if not found.
    """
    match = re.match(r'\s*(.*?\):)', line)
    if match:
        return match.group(1)
    return None

def process_benchmark_line(line1, line2):
    """
    Processes a pair of lines from the bench section.
    
    - If neither line appears to be a benchmark line (i.e. neither contains "GB/s"),
      the function returns line1 as-is.
      
    - Otherwise, it extracts the bench signature (from file1 or file2) and the
      performance (throughput) values from each line. For any missing value, it
      uses an "x". Finally, if both performance numbers are available, it compares
      them (0 if file1's value is higher, 1 if file2's is higher); otherwise, the
      result is "x".
    """
    # If neither line appears to be a benchmark line, print the line as is.
    if "GB/s" not in line1 and "GB/s" not in line2:
        return line1.rstrip()
    
    # Try to extract the bench signature from line1; if missing, try line2.
    ts = extract_test_signature(line1)
    if ts is None:
        ts = extract_test_signature(line2)
    if ts is None:
        ts = line1.rstrip()  # fallback: print the whole line
    
    # For each file, extract throughput if available; otherwise mark as missing.
    if "GB/s" in line1:
        v1, u1 = extract_throughput(line1)
    else:
        v1, u1 = None, ""
    if "GB/s" in line2:
        v2, u2 = extract_throughput(line2)
    else:
        v2, u2 = None, ""
    
    v1_str = str(v1) if v1 is not None else "x"
    v2_str = str(v2) if v2 is not None else "x"
    u1 = u1 if v1 is not None else ""
    u2 = u2 if v2 is not None else ""
    
    # Determine the comparison result if both values are available.
    if v1 is not None and v2 is not None:
        result = 0 if v1 > v2 else 1
    else:
        result = "x"
    
    return f"{ts} {v1_str} {u1}  {v2_str} {u2}  {result}"

def compare_files(file1, file2):
    # Split each file into header, bench, and footer sections.
    header1, bench1, footer1 = split_file(file1)
    header2, bench2, footer2 = split_file(file2)
    
    # Print header from file1 exactly as-is.
    for line in header1:
        print(line, end='')
    print()  # blank line separator
    
    # Process the benchmark lines.
    num_bench_lines = max(len(bench1), len(bench2))
    for i in range(num_bench_lines):
        line1 = bench1[i] if i < len(bench1) else ""
        line2 = bench2[i] if i < len(bench2) else ""
        processed_line = process_benchmark_line(line1, line2)
        print(processed_line)
    
    # Print footer from file1 exactly as-is.
    for line in footer1:
        print(line, end='')

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python compare-backend-ops.py file1.txt file2.txt")
    else:
        compare_files(sys.argv[1], sys.argv[2])

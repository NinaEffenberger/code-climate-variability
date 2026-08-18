import os

# Define the mapping of base directories to their specific year suffixes
tasks = {
    "rsds_future": "2045-2064",
    "wind_future": "2045-2064",
    "rsds_past": "1985-2004",
    "wind_past": "1985-2004",
}

base_path = "../data/ensemble"

with open("merge_commands.sh", "w") as f:
    for folder_suffix, year_range in tasks.items():
        target_dir = os.path.join(base_path, folder_suffix)

        if not os.path.exists(target_dir):
            print(f"Warning: Directory {target_dir} does not exist. Skipping.")
            continue

        for root, dirs, files in os.walk(target_dir):
            # Only act on leaf directories
            if not dirs:
                # Check if the merged file already exists to avoid duplication
                suffix_str = f"_{year_range}"
                if any(suffix_str in file for file in files):
                    continue

                # Filter for .nc files, excluding any that might have been
                # created in previous incomplete runs
                nc_files = [
                    os.path.join(root, file)
                    for file in sorted(files)
                    if file.endswith(".nc") and suffix_str not in file
                ]

                if not nc_files:
                    continue

                # Define the output path
                folder_name = os.path.basename(root)
                output_filename = f"{folder_name}{suffix_str}.nc"
                output_file = os.path.join(root, output_filename)

                # Build CDO command
                input_files = " ".join(f'"{f}"' for f in nc_files)
                cmd = f'cdo mergetime {input_files} "{output_file}"'

                f.write(cmd + "\n")

print("Done! Commands written to merge_commands.sh")

import os

# --- Configuration ---
script_path = "../download_data/ensemble/cdo_commands.sh"
target_grid_low = "../download_data/target_grid_low.txt"
allowed_runs = {"r1i1p1", "r2i1p1", "r3i1p1"}

# Define the different processing tasks (Source, Output, Years)
tasks = [
    # RSDS (Solar)
    (
        "../data/cordex/EUR-11/rcp85/3hr/rsds/SMHI/MPI-M-MPI-ESM-LR/SMHI-RCA4",
        "../data/ensemble/rsds_future",
        range(2055, 2065),
    ),
    (
        "../data/cordex/EUR-11/historical/3hr/rsds/SMHI/MPI-M-MPI-ESM-LR/SMHI-RCA4",
        "../data/ensemble/rsds_past",
        range(1985, 1995),
    ),
    # sfcWind (Wind)
    (
        "../data/cordex/EUR-11/rcp85/3hr/sfcWind/SMHI/MPI-M-MPI-ESM-LR/SMHI-RCA4",
        "../data/ensemble/wind_future",
        range(2055, 2065),
    ),
    (
        "../data/cordex/EUR-11/historical/3hr/sfcWind/SMHI/MPI-M-MPI-ESM-LR/SMHI-RCA4",
        "../data/ensemble/wind_past",
        range(1985, 1995),
    ),
]

# --- Processing ---
# Open with "w" once at the very start to start fresh
with open(script_path, "w") as f:
    f.write("#!/bin/bash\n\n")  # Optional: Add a shebang

    for source_base, output_base_low, year_range in tasks:
        valid_years = [str(y) for y in year_range]

        print(f"Processing: {os.path.basename(output_base_low)}")

        for root, dirs, files in os.walk(source_base):
            current_folder = os.path.basename(root)

            if current_folder not in allowed_runs:
                continue

            for file in files:
                if file.endswith(".nc") and any(y in file for y in valid_years):
                    input_path = os.path.join(root, file)

                    # Determine output path structure
                    rel_path = os.path.relpath(input_path, source_base)
                    rel_dir = os.path.dirname(rel_path)
                    output_dir_low = os.path.join(output_base_low, rel_dir)
                    output_path_low = os.path.join(output_dir_low, file)

                    # Write commands to file
                    f.write(f'mkdir -p "{output_dir_low}"\n')
                    f.write(
                        f'cdo remapbil,{target_grid_low} "{input_path}" "{output_path_low}"\n'
                    )

print(f"\nSuccess! All commands written to: {script_path}")

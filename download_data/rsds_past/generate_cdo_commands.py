import os

# Input and output base paths
source_base = "../data/cordex/EUR-11/historical/3hr/rsds"
output_base_low = "../data/rsds_past"


target_grid_low = "download_data/target_grid_low.txt"

valid_years = [str(y) for y in range(1995, 2005)]  # 1995–2004
allowed_institutes = {"CNRM", "MOHC", "SMHI"}  # Only process these
allowed_run = "r1i1p1"  # Only this last folder

with open("cdo_commands.sh", "w") as f:
    for root, dirs, files in os.walk(source_base):
        for file in files:
            if file.endswith(".nc") and any(y in file for y in valid_years):
                input_path = os.path.join(root, file)

                # Relative path from source base
                rel_path = os.path.relpath(input_path, source_base)
                path_parts = rel_path.split(os.sep)

                # Only process allowed top-level institutes
                top_level = path_parts[0]
                if top_level not in allowed_institutes:
                    continue

                # Only process if the last folder is r1i1p1
                if len(path_parts) > 2 and path_parts[-2] != allowed_run:
                    continue

                # Preserve full folder structure for output
                rel_dir = os.path.dirname(rel_path)
                output_dir_low = os.path.join(output_base_low, rel_dir)
                output_path_low = os.path.join(output_dir_low, file)

                # Ensure output directories exist
                f.write(f'mkdir -p "{output_dir_low}"\n')

                # Generate cdo remapbil command
                f.write(
                    f'cdo remapbil,{target_grid_low} "{input_path}" "{output_path_low}"\n'
                )

print("cdo_commands.sh generated successfully!")

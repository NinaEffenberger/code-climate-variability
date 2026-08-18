import os

base_dir = "../data/rsds_past"

with open("merge_commands.sh", "w") as f:
    for root, dirs, files in os.walk(base_dir):
        # Only act if this is a bottom-most folder (no subdirectories inside)
        if not dirs:
            # Skip if a file with "_2045-2054" already exists in this folder
            if any("_1995-2004" in file for file in files):
                continue

            nc_files = [
                os.path.join(root, file)
                for file in sorted(files)
                if file.endswith(".nc")
            ]

            if not nc_files:
                continue

            # Use the folder name as identifier for the merged output
            folder_name = os.path.basename(root)
            output_file = os.path.join(root, f"{folder_name}_1995-2004.nc")

            # Build command
            input_files = " ".join(f'"{f}"' for f in nc_files)
            cmd = f'cdo mergetime {input_files} "{output_file}"'

            f.write(cmd + "\n")

To run the src files, the original CMIP6 data is required. Data can be downloaded from the ESGF nodes. 

For each of the subfolders (wind and rsds, past and future), data of the same resolution and extent can be generated using these commands in the given order

```bash
# generate CDO commands
python generate_cdo_commands

# Activate .sh file
chmod +x cdo_commands.sh

# Run .sh file 
./cdo_commands.sh

# Merge files
python merge_files.py

# Activate .sh file
chmod +x merge_commands.sh

# Run .sh file 
./merge_commands.sh
```

You can then delete the individual files, e.g. 

```bash
find "$base_dir" -type f -name "*.nc" ! -name "*1995-2004*" -exec rm -v {} \;
```
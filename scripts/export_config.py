#!/usr/bin/env python3
"""Read a YAML config file and export key values as environment variables to GITHUB_ENV.
Usage: python scripts/export_config.py configs/dev.yml
Writes keys as UPPERCASE and replaces non-alphanumeric with underscore.
"""
import sys
import yaml
import os
import re

if len(sys.argv) < 2:
    print("Usage: export_config.py <config.yml>")
    sys.exit(2)

cfg_path = sys.argv[1]
if not os.path.exists(cfg_path):
    print(f"Config file not found: {cfg_path}")
    sys.exit(1)

with open(cfg_path) as f:
    cfg = yaml.safe_load(f) or {}

github_env = os.environ.get('GITHUB_ENV')
if not github_env:
    # For local testing fallback to env
    for k,v in cfg.items():
        key = re.sub('[^0-9a-zA-Z]+','_', k).upper()
        os.environ[key] = str(v)
    print("Exported config to process environment (no GITHUB_ENV set).")
else:
    with open(github_env, 'a') as out:
        for k,v in cfg.items():
            key = re.sub('[^0-9a-zA-Z]+','_', k).upper()
            out.write(f"{key}={v}\n")
    print(f"Exported config values to GITHUB_ENV from {cfg_path}")

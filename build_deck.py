#!/usr/bin/env python
"""
CLI entry point for dt-ppt-builder.

Usage:
    py build_deck.py --config configs/example/config.yaml
    py build_deck.py --config configs/example/config.yaml --output C:\\temp\\deck.pptx
"""
import argparse
import sys
import os

# Allow running from repo root without installing the package
sys.path.insert(0, os.path.dirname(__file__))

from dt_ppt_builder.builder import build


def main():
    parser = argparse.ArgumentParser(
        description="Build a Dynatrace-branded PPTX from a YAML config.")
    parser.add_argument(
        "--config", required=True,
        help="Path to the customer config YAML file  (e.g. configs/example/config.yaml)")
    parser.add_argument(
        "--output", default=None,
        help="Override output path from the config file")
    args = parser.parse_args()

    # Optional output override
    if args.output:
        import yaml
        with open(args.config, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        cfg["output"] = args.output
        # Write a temporary patched config
        import tempfile, json
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml",
                                          delete=False, encoding="utf-8")
        yaml.dump(cfg, tmp, allow_unicode=True)
        tmp.close()
        print(f"[build_deck] Output overridden → {args.output}")
        build(tmp.name)
        os.unlink(tmp.name)
    else:
        build(args.config)


if __name__ == "__main__":
    main()

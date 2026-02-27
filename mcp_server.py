#!/usr/bin/env python3
"""
dt-ppt-builder MCP Server
==========================
Exposes the Dynatrace PPT builder as a set of MCP tools for
GitHub Copilot, VS Code, or any MCP-compatible client.

Tools:
  1. build_deck          — generate a branded PPTX from dynamic slide content
  2. build_customer_deck — generate a PPTX from a pre-built customer config
  3. list_customers      — show available customer configs
  4. parse_excel         — convert a requirements Excel file to JSON
  5. create_customer     — scaffold a new customer config directory
  6. get_requirements    — read a customer's requirements.json

Transport: stdio  (works with Copilot Chat, VS Code, Claude Desktop, etc.)

Start:
    py mcp_server.py
"""

import asyncio
import json
import os
import sys

# Ensure the package is importable when running from repo root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
)

import yaml

# Package root = where this script lives
PKG_ROOT    = os.path.dirname(os.path.abspath(__file__))
CONFIGS_DIR = os.path.join(PKG_ROOT, "configs")

server = Server("dt-ppt-builder")


# ─────────────────────────────────────────────────────────────────────────────
# Tool definitions
# ─────────────────────────────────────────────────────────────────────────────
SLIDE_TYPE_DOCS = (
    "Supported slide types:\n"
    "  • title        — {title, subtitle?, contact?}\n"
    "  • section      — {title, subtitle?}  (chapter divider)\n"
    "  • bullets      — {title, eyebrow?, bullets: [str]}\n"
    "  • table        — {title, eyebrow?, columns: [str], rows: [[str]]}\n"
    "  • two_column   — {title, left_header?, left_bullets, right_header?, right_bullets}\n"
    "  • text         — {title, eyebrow?, body: str}\n"
    "  • image        — {title, image_path, caption?}\n"
    "  • comparison   — {title, items: [{label, bullets}]}\n"
    "  • closing      — {message?, contact?}\n"
    "  • hero         — {brand, headline, sub_headline?, tagline?}  (full-bleed opening)\n"
    "  • card_grid    — {title, eyebrow?, cards: [{icon, title, description}], footer?}\n"
    "  • icon_bullets — {title, eyebrow?, subtitle?, bullets: [str], image_path?, footer?}\n"
    "  • split_panel  — {title, eyebrow?, bullets, panel_title, panel_items, footer?}\n"
    "  • two_image    — {title, eyebrow?, left_image, left_caption?, right_image, right_caption?, footer?}\n"
    "  • value_props  — {title, eyebrow?, props: [{icon, title, description}]}\n"
    "  • cta          — {brand?, headline, sub_text?, cta_text?}  (call-to-action closing)"
)

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        # ── PRIMARY: dynamic content-driven deck builder ─────────────────
        Tool(
            name="build_deck",
            description=(
                "Build a Dynatrace-branded PPTX slide deck from dynamic content. "
                "YOU generate the slide content — the tool renders it with "
                "Dynatrace branding and saves the PPTX.\n\n"
                "Pass an array of slide spec objects. Each has a 'type' field "
                "plus type-specific content fields.\n\n"
                + SLIDE_TYPE_DOCS
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "template_path": {
                        "type": "string",
                        "description": (
                            "Absolute path to a .pptx or .potx template file. "
                            "This provides the slide masters, backgrounds, and fonts."
                        ),
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Absolute path where the generated .pptx should be saved.",
                    },
                    "slides": {
                        "type": "array",
                        "description": (
                            "Array of slide spec objects. Each must have a 'type' "
                            "field (title/section/bullets/table/two_column/text/"
                            "image/comparison/closing) plus type-specific content."
                        ),
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "enum": [
                                        "title", "section", "bullets", "table",
                                        "two_column", "text", "image",
                                        "comparison", "closing"
                                    ],
                                },
                            },
                            "required": ["type"],
                        },
                    },
                    "layout_indices": {
                        "type": "object",
                        "description": (
                            "Optional. Override default layout index mapping. "
                            "Keys: title_center (default 11), title_content (default 2), "
                            "two_img (default 19). Adjust for your template."
                        ),
                    },
                },
                "required": ["template_path", "output_path", "slides"],
            },
        ),

        # ── Config-based deck builder (pre-built customer configs) ───────
        Tool(
            name="build_customer_deck",
            description=(
                "Build a Dynatrace-branded PPTX from a pre-built customer config. "
                "The customer must have a config.yaml and requirements.json under "
                "configs/<customer>/. Use list_customers to see available configs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "customer": {
                        "type": "string",
                        "description": (
                            "Customer name matching a folder under configs/ "
                            "(e.g. 'example'). Use list_customers to see options."
                        ),
                    },
                    "output_path": {
                        "type": "string",
                        "description": (
                            "Optional override for the output .pptx file path. "
                            "If omitted, uses the path from the customer's config.yaml."
                        ),
                    },
                    "config_overrides": {
                        "type": "object",
                        "description": (
                            "Optional dict of config keys to override "
                            "(e.g. deck_title, deck_subtitle, closing_message)."
                        ),
                    },
                },
                "required": ["customer"],
            },
        ),

        Tool(
            name="list_customers",
            description=(
                "List all available pre-built customer configurations. "
                "These can be used with build_customer_deck."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),

        Tool(
            name="parse_excel",
            description=(
                "Parse a customer requirements Excel file (.xlsx) into the "
                "canonical JSON structure used by build_customer_deck. "
                "Supports multi-sheet or single-sheet formats."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "excel_path": {
                        "type": "string",
                        "description": "Absolute path to the .xlsx file.",
                    },
                    "output_json_path": {
                        "type": "string",
                        "description": (
                            "Optional path to save the parsed JSON. "
                            "If omitted, returns JSON in the response only."
                        ),
                    },
                },
                "required": ["excel_path"],
            },
        ),

        Tool(
            name="create_customer",
            description=(
                "Scaffold a new customer configuration directory under configs/. "
                "Creates config.yaml with sensible defaults and an empty "
                "requirements.json."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "customer": {
                        "type": "string",
                        "description": "Customer name (used as folder name, e.g. 'acme').",
                    },
                    "template_path": {
                        "type": "string",
                        "description": "Absolute path to the .pptx or .potx template file.",
                    },
                    "deck_title": {
                        "type": "string",
                        "description": "Title for the deck (default: 'Dynatrace AI Observability').",
                    },
                    "screenshots_dir": {
                        "type": "string",
                        "description": "Optional path to a directory containing screenshot images.",
                    },
                },
                "required": ["customer", "template_path"],
            },
        ),

        Tool(
            name="get_requirements",
            description=(
                "Read a customer's requirements.json and return a summary: "
                "domain names, requirement counts, and coverage statistics."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "customer": {
                        "type": "string",
                        "description": "Customer name matching a folder under configs/.",
                    },
                },
                "required": ["customer"],
            },
        ),
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Tool dispatch
# ─────────────────────────────────────────────────────────────────────────────
@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "build_deck":
            return _build_deck_generic(arguments)
        elif name == "build_customer_deck":
            return _build_customer_deck(arguments)
        elif name == "list_customers":
            return _list_customers()
        elif name == "parse_excel":
            return _parse_excel(arguments)
        elif name == "create_customer":
            return _create_customer(arguments)
        elif name == "get_requirements":
            return _get_requirements(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error: {e}")]


# ─────────────────────────────────────────────────────────────────────────────
# build_deck — dynamic/generic (PRIMARY)
# ─────────────────────────────────────────────────────────────────────────────
def _build_deck_generic(args: dict) -> list[TextContent]:
    template_path  = args["template_path"]
    output_path    = args["output_path"]
    slides         = args["slides"]
    layout_indices = args.get("layout_indices")

    if not os.path.isfile(template_path):
        return [TextContent(type="text",
                text=f"❌ Template not found: {template_path}")]

    from dt_ppt_builder.builder import build_generic
    result = build_generic(template_path, slides, output_path, layout_indices)

    return [TextContent(type="text",
            text=f"✅ Deck built successfully!\n\n"
                 f"📄 **Output:** {result}\n"
                 f"📊 **Slides:** {len(slides)}")]


# ─────────────────────────────────────────────────────────────────────────────
# build_customer_deck — config-based (for pre-built customer configs)
# ─────────────────────────────────────────────────────────────────────────────
def _build_customer_deck(args: dict) -> list[TextContent]:
    customer = args["customer"]
    config_path = os.path.join(CONFIGS_DIR, customer, "config.yaml")

    if not os.path.isfile(config_path):
        return [TextContent(type="text",
                text=f"❌ No config found for '{customer}'. "
                     f"Available: {_customer_names()}")]

    with open(config_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    overrides = args.get("config_overrides") or {}
    cfg.update(overrides)

    if args.get("output_path"):
        cfg["output"] = args["output_path"]

    config_dir = os.path.join(CONFIGS_DIR, customer)
    req_path = cfg.get("requirements_file") or "requirements.json"
    if not os.path.isabs(req_path):
        req_path = os.path.join(config_dir, req_path)

    if not os.path.isfile(req_path):
        return [TextContent(type="text",
                text=f"❌ Requirements file not found: {req_path}\n"
                     f"Use parse_excel to create one from an .xlsx file.")]

    with open(req_path, encoding="utf-8") as f:
        req_data = json.load(f)

    from dt_ppt_builder.builder import build_and_save
    output = cfg.get("output", os.path.join(config_dir, f"{customer}_deck.pptx"))
    result = build_and_save(cfg, req_data, output)

    return [TextContent(type="text",
            text=f"✅ Deck built successfully!\n\n"
                 f"📄 **Output:** {result}\n"
                 f"📊 **Domains:** {len(req_data)}\n"
                 f"📋 **Requirements:** {sum(len(d['reqs']) for d in req_data)}")]


# ─────────────────────────────────────────────────────────────────────────────
# list_customers
# ─────────────────────────────────────────────────────────────────────────────
def _list_customers() -> list[TextContent]:
    if not os.path.isdir(CONFIGS_DIR):
        return [TextContent(type="text", text="No configs/ directory found.")]

    customers = []
    for entry in sorted(os.listdir(CONFIGS_DIR)):
        cfg_path = os.path.join(CONFIGS_DIR, entry, "config.yaml")
        if os.path.isfile(cfg_path):
            with open(cfg_path, encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
            req_path = os.path.join(CONFIGS_DIR, entry, "requirements.json")
            has_reqs = os.path.isfile(req_path)
            customers.append({
                "name": entry,
                "customer": cfg.get("customer", entry),
                "deck_title": cfg.get("deck_title", ""),
                "has_requirements": has_reqs,
            })

    if not customers:
        return [TextContent(type="text", text="No customer configs found under configs/.")]

    lines = ["**Available Customer Configs:**\n"]
    for c in customers:
        status = "✅ Ready" if c["has_requirements"] else "⚠️ No requirements.json"
        lines.append(
            f"- **{c['name']}** — {c['customer']} "
            f"({c['deck_title']}) [{status}]"
        )
    return [TextContent(type="text", text="\n".join(lines))]


# ─────────────────────────────────────────────────────────────────────────────
# parse_excel
# ─────────────────────────────────────────────────────────────────────────────
def _parse_excel(args: dict) -> list[TextContent]:
    excel_path = args["excel_path"]
    output_json = args.get("output_json_path")

    if not os.path.isfile(excel_path):
        return [TextContent(type="text",
                text=f"❌ Excel file not found: {excel_path}")]

    from dt_ppt_builder.excel_parser import parse_excel, parse_excel_to_json

    if output_json:
        json_str = parse_excel_to_json(excel_path, output_json)
        data = json.loads(json_str)
        lines = [f"✅ Parsed and saved to: {output_json}\n"]
    else:
        data = parse_excel(excel_path)
        lines = ["✅ Parsed successfully (not saved to disk).\n"]

    total_reqs = sum(len(d["reqs"]) for d in data)
    lines.append(f"**{len(data)} domains, {total_reqs} requirements total**\n")
    for d in data:
        reqs = d["reqs"]
        now     = sum(1 for r in reqs if "✅" in r.get("status", ""))
        partial = sum(1 for r in reqs if "⚡" in r.get("status", ""))
        roadmap = sum(1 for r in reqs if "🗺" in r.get("status", ""))
        lines.append(
            f"- {d['name']}: {len(reqs)} reqs "
            f"(✅ {now} · ⚡ {partial} · 🗺 {roadmap})"
        )

    return [TextContent(type="text", text="\n".join(lines))]


# ─────────────────────────────────────────────────────────────────────────────
# create_customer
# ─────────────────────────────────────────────────────────────────────────────
def _create_customer(args: dict) -> list[TextContent]:
    customer = args["customer"].strip().lower().replace(" ", "-")
    template_path = args["template_path"]
    deck_title = args.get("deck_title", "Dynatrace AI Observability")
    screenshots_dir = args.get("screenshots_dir", "")

    cust_dir = os.path.join(CONFIGS_DIR, customer)
    if os.path.exists(cust_dir):
        return [TextContent(type="text",
                text=f"⚠️ Config directory already exists: {cust_dir}")]

    os.makedirs(cust_dir, exist_ok=True)

    cfg = {
        "customer": customer.replace("-", " ").title(),
        "deck_title": deck_title,
        "deck_subtitle": f"AI OBSERVABILITY · {customer.upper()} · 2026",
        "contact": "Prepared by Dynatrace SE Team",
        "closing_message": "One Platform. Every AI Signal.",
        "template": template_path,
        "output": os.path.join(cust_dir, f"{customer}_deck.pptx"),
        "layout_indices": {
            "title_center": 11,
            "title_content": 2,
            "two_img": 19,
        },
        "screenshots_dir": screenshots_dir,
        "images": {},
        "screenshot_slides": [],
        "requirements_file": "requirements.json",
    }

    cfg_path = os.path.join(cust_dir, "config.yaml")
    with open(cfg_path, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)

    req_path = os.path.join(cust_dir, "requirements.json")
    with open(req_path, "w", encoding="utf-8") as f:
        json.dump([], f)

    return [TextContent(type="text",
            text=f"✅ Customer scaffolded: {cust_dir}\n\n"
                 f"**Created files:**\n"
                 f"- {cfg_path}\n"
                 f"- {req_path}\n\n"
                 f"**Next steps:**\n"
                 f"1. Add requirements: use `parse_excel` to populate requirements.json\n"
                 f"2. Edit config.yaml: set layout_indices for your template\n"
                 f"3. Build: use `build_customer_deck` with customer='{customer}'")]


# ─────────────────────────────────────────────────────────────────────────────
# get_requirements
# ─────────────────────────────────────────────────────────────────────────────
def _get_requirements(args: dict) -> list[TextContent]:
    customer = args["customer"]
    config_dir = os.path.join(CONFIGS_DIR, customer)
    req_path = os.path.join(config_dir, "requirements.json")

    if not os.path.isfile(req_path):
        return [TextContent(type="text",
                text=f"❌ No requirements.json for '{customer}'")]

    with open(req_path, encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        return [TextContent(type="text",
                text=f"⚠️ requirements.json for '{customer}' is empty.")]

    total = sum(len(d["reqs"]) for d in data)
    now     = sum(1 for d in data for r in d["reqs"] if "✅" in r.get("status",""))
    partial = sum(1 for d in data for r in d["reqs"] if "⚡" in r.get("status",""))
    roadmap = sum(1 for d in data for r in d["reqs"] if "🗺" in r.get("status",""))
    pct = round(now / total * 100) if total else 0

    lines = [
        f"**{customer.title()} Requirements Summary**\n",
        f"📊 {total} total requirements across {len(data)} domains",
        f"✅ {now} available now ({pct}%)",
        f"⚡ {partial} partially available",
        f"🗺 {roadmap} on roadmap\n",
        "**Domains:**",
    ]

    for d in data:
        reqs = d["reqs"]
        d_now = sum(1 for r in reqs if "✅" in r.get("status",""))
        d_part = sum(1 for r in reqs if "⚡" in r.get("status",""))
        d_road = sum(1 for r in reqs if "🗺" in r.get("status",""))
        lines.append(
            f"- {d['name']}: {len(reqs)} reqs "
            f"(✅ {d_now} · ⚡ {d_part} · 🗺 {d_road})"
        )

    return [TextContent(type="text", text="\n".join(lines))]


# ─────────────────────────────────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────────────────────────────────
def _customer_names() -> str:
    if not os.path.isdir(CONFIGS_DIR):
        return "(none)"
    names = [e for e in os.listdir(CONFIGS_DIR)
             if os.path.isdir(os.path.join(CONFIGS_DIR, e))]
    return ", ".join(names) if names else "(none)"


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())

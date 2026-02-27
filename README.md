# dt-ppt-builder

Reusable Dynatrace-branded PPTX generator — available as **CLI**, **Python library**, and **MCP tool server** for GitHub Copilot / VS Code / Claude Desktop.

Drop in a customer config + requirements JSON → get a polished slide deck out.

---

## Quick start (CLI)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Build a deck
py build_deck.py --config configs/example/config.yaml

# 3. Optional: override output path on the fly
py build_deck.py --config configs/example/config.yaml --output C:\temp\test.pptx
```

---

## MCP Server (GitHub Copilot / VS Code / Claude Desktop)

The MCP server exposes the PPT builder as tools that any MCP-compatible AI client
can call. Your colleagues can type natural language in Copilot Chat and the tool
generates branded decks automatically.

### Setup

**1. Install dependencies:**
```bash
cd dt-ppt-builder
pip install -r requirements.txt
```

**2. Configure in VS Code** — add to `.vscode/mcp.json` (workspace) or User Settings:
```json
{
  "servers": {
    "dt-ppt-builder": {
      "command": "py",
      "args": ["c:\\repos\\dt-ppt-builder\\mcp_server.py"],
      "env": {}
    }
  }
}
```

**3. Configure in Claude Desktop** — add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "dt-ppt-builder": {
      "command": "py",
      "args": ["c:\\repos\\dt-ppt-builder\\mcp_server.py"]
    }
  }
}
```

### Available MCP Tools

| Tool | Description | Example prompt |
|---|---|---|
| `list_customers` | Show all available customer configs | *"What customers have PPT configs?"* |
| `build_deck` | Generate a PPTX from a customer config | *"Build the Acme Corp AI observability deck"* |
| `parse_excel` | Convert a requirements .xlsx to JSON | *"Parse C:\data\Acme_Metrics.xlsx into requirements JSON"* |
| `create_customer` | Scaffold a new customer config directory | *"Create a new customer config for Acme Corp"* |
| `get_requirements` | Show requirement summary & coverage stats | *"Show me the Acme Corp requirement coverage"* |

### Example Copilot Chat conversations

```
You:     "Build the Acme Corp deck"
Copilot: → calls build_deck(customer="example")
         ✅ Deck built: configs/example/example_deck.pptx (8.2 MB, 14 slides)
```

```
You:     "Parse C:\data\NewCo_Metrics.xlsx and save as requirements JSON"
Copilot: → calls parse_excel(excel_path="C:\data\NewCo_Metrics.xlsx",
                             output_json_path="configs/newco/requirements.json")
         ✅ Parsed: 6 domains, 112 requirements
```

```
You:     "Set up a new customer called 'acme' using the Corporate 2026 template"
Copilot: → calls create_customer(customer="acme",
                                 template_path="C:\templates\Corporate_2026.potx")
         ✅ Scaffolded: configs/acme/config.yaml + requirements.json
```

---

## Repository layout

```
dt-ppt-builder/
├── mcp_server.py          — MCP tool server (stdio transport)
├── build_deck.py          — CLI entry point
├── requirements.txt
├── README.md
├── dt_ppt_builder/
│   ├── __init__.py        — package exports
│   ├── brand.py           — Dynatrace RGB colors + status_color()
│   ├── helpers.py         — low-level drawing: txb, req_table, status_bar …
│   ├── slide_builder.py   — slide factories: title, coverage, domain …
│   ├── builder.py         — orchestrator: config → deck → save / bytes
│   └── excel_parser.py    — Excel → requirements JSON converter
├── configs/
│   └── example/
│       ├── config.yaml        — paths, metadata, layout indices
│       └── requirements.json  — 134 requirements across 6 domains
```

---

## Adding a new customer

### Option A: Via MCP (recommended)
1. Ask Copilot: *"Create a new customer config for Acme Corp"*
2. Ask Copilot: *"Parse C:\data\Acme_Metrics.xlsx and save to configs/acme/requirements.json"*
3. Edit `configs/acme/config.yaml` to set layout indices, screenshots, etc.
4. Ask Copilot: *"Build the Acme deck"*

### Option B: Manual
1. Create `configs/<customer>/` directory.
2. Copy `configs/example/config.yaml` and edit:
   - `customer`, `deck_title`, `deck_subtitle`, `contact`
   - `template` (PPTX template path)
   - `output` (where to save)
   - `screenshots_dir` + `images` keys
   - `screenshot_slides` list
3. Create `configs/<customer>/requirements.json` — same structure as the example:
   ```json
   [
     {
       "name": "Domain 1 of N · <Domain Name>",
       "description": "<short scope>",
       "reqs": [
         { "requirement": "...", "description": "...", "status": "✅ Now", "signal": "TRACE" },
         ...
       ]
     }
   ]
   ```
4. Run: `py build_deck.py --config configs/<customer>/config.yaml`

---

## Status values

| Value | Badge color | Meaning |
|---|---|---|
| `✅ Now` | Green | Available in current Dynatrace release |
| `⚡ Partial` | Orange | Partially covered; additional config/extension needed |
| `🗺 Roadmap` | Gray | On product roadmap; not yet GA |

---

## Layout index reference (Perform 2026 template)

| Key | Default idx | Layout name (approx.) |
|---|---|---|
| `title_center` | 11 | Title + eyebrow only, centered |
| `title_content` | 2 | Title + eyebrow + content, center |
| `two_img` | 19 | 2 images + captions |

Override in `config.yaml` under `layout_indices:` if using a different template.

---

## Key design decisions

- **No template content reuse** — every slide is built from scratch; the template only provides brand background, fonts and colour palette.
- **Corruption-safe slide clearing** — `prs.part.drop_rel(rId)` is called before `sldIdLst.remove(sId)` to avoid duplicate zip entries that force PowerPoint repair.
- **Config-driven** — YAML controls all paths and metadata; customer data lives in JSON; code is customer-agnostic.
- **MCP-first** — designed to be called by AI agents; all tools return structured text responses.

---

## Dependencies

| Package | Purpose |
|---|---|
| `python-pptx` | PPTX generation |
| `Pillow` | Image embedding |
| `PyYAML` | Config file parsing |
| `mcp` | MCP server SDK (stdio transport) |
| `openpyxl` | Excel requirements parser |
| `lxml` | XML manipulation for template handling |

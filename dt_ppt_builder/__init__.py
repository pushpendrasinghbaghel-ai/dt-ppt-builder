"""dt_ppt_builder — reusable Dynatrace-branded PPT builder package."""
from .brand import (WHITE, TEAL, GREEN, ORANGE, PURPLE, GRAY, LGRAY, DGRAY,
                    DDGRAY, DTDARK, STATUS_COLOR, status_color, RGBColor)
from .helpers import (set_ph, txb, para_block, status_bar, req_table,
                      add_img, coverage_table)
from .builder import build, build_from_dict, build_and_save, build_generic, build_generic_bytes
from .excel_parser import parse_excel, parse_excel_to_json
from .generic_slides import render_slide, render_all

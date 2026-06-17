import sys
from pathlib import Path

sys.path.insert(0, str((Path(__file__).parent / "../../src").resolve()))

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "pypana"
copyright = "2026, Maximilian Böhmichen, Kevin Maier"
author = "Maximilian Böhmichen, Kevin Maier"
release = "0.0.1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.coverage",
    "sphinxcontrib.cairosvgconverter",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinxcontrib.autodoc_pydantic",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns: list[str] = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "pydata_sphinx_theme"
html_theme_options = {
    "pygments_light_style": "default",
    "pygments_dark_style": "monokai",
}
html_static_path = ["_static"]

maximum_signature_line_length = 88
autodoc_preserve_defaults = True
autodoc_typehints = "description"
autosummary_generate = True
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    "member-order": "bysource",
}

autodoc_pydantic_model_show_config_summary = False
autodoc_pydantic_model_show_validator_summary = False
autodoc_pydantic_model_show_json = False

latex_engine = "xelatex"

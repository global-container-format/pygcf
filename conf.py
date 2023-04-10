from os import path

import toml


CONF_DIR = path.dirname(__file__)
PYPROJECT_FILE = path.join(CONF_DIR, "pyproject.toml")


with open(PYPROJECT_FILE) as f:
    pyproject_data = toml.load(f)

py_project = pyproject_data["project"]
py_tool_sphinx = pyproject_data["tool"]["sphinx"]

globals().update(py_tool_sphinx)


# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = py_project["name"]
author = ", ".join(map(lambda auth: auth["name"], py_project["authors"]))
copyright = f"2023, ${author}"
release = py_project["version"]

# Keep this a plain string literal with no imports around it: pyproject reads it
# statically (setuptools dynamic version via AST, no import) as the package
# version. A computed expression would force setuptools to import the package at
# build time, pulling in the runtime deps (mcp, pydantic, requests).
__version__ = "1.0.0"

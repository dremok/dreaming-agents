# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- `pip install -r requirements.txt`
- Lint: `python -m flake8 multi_tool_agent/`
- Type check: `python -m mypy multi_tool_agent/`
- Run agent: Use Google ADK CLI commands (adk deploy, adk run)

## Code Style
- Python: Follow PEP 8 guidelines
- Imports: Standard library first, then third-party, then local
- Use Google ADK imports like `from google.adk.agents import Agent`
- Use type hints for function parameters and return values
- Class/function names: snake_case for functions, CamelCase for classes
- String formatting: Use f-strings for string interpolation
- Error handling: Use try/except blocks with specific exceptions
- Documentation: Use docstrings for functions and classes

## Project Structure
- Keep agent definitions in separate files when using multiple agents
- Store agent tools in a dedicated module or directory
- Instructions for agents should be well-formatted and comprehensive

## Workflow
- Prefer running single tests, and not the whole test suite, for performance
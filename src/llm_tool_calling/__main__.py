"""Allow running as: python -m llm_tool_calling"""
from dotenv import load_dotenv

load_dotenv()

from .runner import main

main()

#!/usr/bin/env python3
"""
Main entry point for IRIS Detection Service
"""
import asyncio

# Import from src package (no path manipulation needed)
from src.controller import main

if __name__ == "__main__":
    asyncio.run(main())

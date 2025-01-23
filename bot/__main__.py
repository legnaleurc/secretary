import asyncio
import sys

from .main import amain


sys.exit(asyncio.run(amain()))

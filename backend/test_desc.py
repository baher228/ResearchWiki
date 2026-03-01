import asyncio
import os
import sys

# add backend path so we can import app
sys.path.insert(0, r"c:\Users\1\ResearchWiki\backend")

from app.services.description_service import get_description

async def main():
    try:
        response = await get_description("This is a test text to summarize.")
        print("SUCCESS:", response)
    except Exception as e:
        print("ERROR:", repr(e))

if __name__ == "__main__":
    asyncio.run(main())

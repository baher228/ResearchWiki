#TEST SCRIPT

import asyncio
import json

from mistralai import Mistral

from app.config import get_settings

async def main():
    settings = get_settings()
    client = Mistral(api_key=settings.MISTRAL_API_KEY)

    response = await client.chat.complete_async(
        model=settings.MISTRAL_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"},
        ],
    )

    print(response.choices[0].message.content)

if __name__ == "__main__":
    asyncio.run(main())
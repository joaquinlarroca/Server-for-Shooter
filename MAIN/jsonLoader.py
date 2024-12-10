import asyncio
import json
import aiofiles
import sys
import os

import color

os.chdir(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print(color.FAIL + "THIS IS NOT THE MAIN PY FILE" + color.ENDC)
    sys.exit()

json_empty = {}

async def load(filename="config",emptyFileSample = json_empty):
    try:
        async with aiofiles.open(filename + ".json", mode='r') as file:
            x = await file.read()
            return json.loads(x)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"File {filename}.json not found")
        async with aiofiles.open(filename + ".json", mode="w") as f:
            try:
                await f.write(json.dumps(emptyFileSample, indent=4))
            except Exception as e:
                print(f"Error writing data: {e}")
        return emptyFileSample
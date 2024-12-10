import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import sqlite_handler as sqlh

async def main():
    print("Enter the ID of the user:")
    Userid = int(input())
    user = await sqlh.getUserFromID(Userid)
    print(f"{user}? (y/n)")
    answer = input()
    if answer == "y" or answer == "Y":
        await ban(Userid)
        

if __name__ == "__main__":
    asyncio.run(main())
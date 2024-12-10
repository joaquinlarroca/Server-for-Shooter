import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import sqlite_handler as sqlh


async def ban(id: int):
    if(await sqlh.getUserTagFromID(id) == "BANNED"):
        print("User is already banned")
        
    else:
        await sqlh.updateUserTag(id, "BANNED")
        print("User banned")


async def unban(id: int):
    if(await sqlh.getUserTagFromID(id) == "BANNED"):
        await sqlh.updateUserTag(id, "DEFAULT")
        print("User unbanned")
    else:
        print("User is not banned")

async def main():
    print("Enter the ID of the user you want to ban:")
    Userid = int(input())
    user = await sqlh.getUserFromID(Userid)
    print(f"Do you want to ban {user}? (y/n)")
    answer = input()
    if answer == "y" or answer == "Y":
        await ban(Userid)
        

if __name__ == "__main__":
    asyncio.run(main())
import aiosqlite
import os
import sys

import color


os.chdir(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print(color.FAIL + "THIS IS NOT THE MAIN PY FILE" + color.ENDC)
    sys.exit()

dbTablesTypes = {
    "users": f"""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            tag TEXT NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            coins INTEGER NOT NULL,
            banner INTEGER NOT NULL
        )""" 
}
dbConfig = {
    "DATABASE": "server",
}

async def createTable(name: str):
    if not os.path.exists("database"):
        os.mkdir("database")
    query = dbTablesTypes[name]
    async with aiosqlite.connect(f"./database/{dbConfig['DATABASE']}.db") as db:
        async with db.cursor() as cursor:
            await cursor.execute(query)
            await db.commit()


async def addUser(name: str, hashed_password: str):
    async with aiosqlite.connect(f"./database/{dbConfig['DATABASE']}.db") as db:
        async with db.cursor() as cursor:
            await cursor.execute(
                f"SELECT EXISTS(SELECT 1 FROM users WHERE username = ?)",
                (name,),
            )
            rows = await cursor.fetchone()
            if rows[0] == 0:
                await cursor.execute(
                    f"INSERT INTO users (tag, username,  password, coins, banner) VALUES (?, ?, ?, ?, ?)",
                    ("DEFAULT", name, hashed_password, 0, 0),
                )
                await db.commit()
                return True
            else:
                return False

async def getUserIDFromName(name: str):
    async with aiosqlite.connect(f"./database/{dbConfig['DATABASE']}.db") as db:
        async with db.cursor() as cursor:
            await cursor.execute(
                f"SELECT id FROM users WHERE username = ?",
                (name,),
            )
            rows = await cursor.fetchone()
            if rows is None:
                return False
            return rows[0]

async def getUserFromID(id: int):
    async with aiosqlite.connect(f"./database/{dbConfig['DATABASE']}.db") as db:
        async with db.cursor() as cursor:
            await cursor.execute(
                f"SELECT username FROM users WHERE id = ?",
                (id,),
            )
            rows = await cursor.fetchone()
            if rows is None:
                return False
            return rows[0]

async def getDataFromID(id: int):
    async with aiosqlite.connect(f"./database/{dbConfig['DATABASE']}.db") as db:
        async with db.cursor() as cursor:
            await cursor.execute(
                f"SELECT * FROM users WHERE id = ?",
                (id,),
            )
            rows = await cursor.fetchone()
            rows = list(rows)
            rows[3] = "********"
            return rows
        
async def getPasswordFromID(id: int):
    async with aiosqlite.connect(f"./database/{dbConfig['DATABASE']}.db") as db:
        async with db.cursor() as cursor:
            await cursor.execute(
                f"SELECT password FROM users WHERE id = ?",
                (id,),
            )
            rows = await cursor.fetchone()
            rows = list(rows)
            return rows[0]

async def updateUserPassword(id: int, password: str):
    async with aiosqlite.connect(f"./database/{dbConfig['DATABASE']}.db") as db:
        async with db.cursor() as cursor:
            await cursor.execute(
                f"UPDATE users SET password = ? WHERE id = ?",
                (password, id),
            )
            await db.commit()

async def getUserTagFromID(id: int):
    async with aiosqlite.connect(f"./database/{dbConfig['DATABASE']}.db") as db:
        async with db.cursor() as cursor:
            await cursor.execute(
                f"SELECT tag FROM users WHERE id = ?",
                (id,),
            )
            rows = await cursor.fetchone()
            if rows is None:
                return False
            return rows[0]
        
async def updateUserTag(id: int, tag: str):
    async with aiosqlite.connect(f"./database/{dbConfig['DATABASE']}.db") as db:
        async with db.cursor() as cursor:
            await cursor.execute(
                f"UPDATE users SET tag = ? WHERE id = ?",
                (tag, id),
            )
            await db.commit()

async def start():
    for tables in dbTablesTypes:
        await createTable(tables)


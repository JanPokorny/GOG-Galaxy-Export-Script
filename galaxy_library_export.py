import sqlite3
import json
import time
import csv


database_location = "C:\\ProgramData\\GOG.com\\Galaxy\\storage\\galaxy-2.0.db"
platforms = { "3do": "3DO Interactive", "3ds": "Nintendo 3DS", "aion": "Aion", "aionl": "Aion: Legions of War", "amazon": "Amazon", "amiga": "Amiga", "arc": "ARC", "atari": "Atari", "battlenet": "Battle.net", "bb": "BestBuy", "beamdog": "Beamdog", "bethesda": "Bethesda.net", "blade": "Blade & Soul", "c64": "Commodore 64", "d2d": "Direct2Drive", "dc": "Sega Dreamcast", "discord": "Discord", "dotemu": "DotEmu", "egg": "Newegg", "elites": "Elite Dangerous", "epic": "Epic Games Store", "eso": "ESO", "fanatical": "Fanatical store", "ffxi": "Final Fantasy XI", "ffxiv": "Final Fantasy XIV", "fxstore": "Placeholder", "gamehouse": "GameHouse", "gamesessions": "GameSessions", "gameuk": "Game UK", "generic": "Other", "gg": "GamersGate", "glyph": "Trion World", "gmg": "Green Man Gaming", "gog": "GOG", "gw": "Guild Wars", "gw2": "Guild Wars 2", "humble": "Humble Bundle", "indiegala": "IndieGala", "itch": "Itch.io", "jaguar": "Atari Jaguar", "kartridge": "Kartridge", "lin2": "Lineage 2", "minecraft": "Minecraft", "n64": "Nintendo64", "ncube": "Nintendo GameCube", "nds": "Nintendo DS", "neo": "NeoGeo", "nes": "NES", "ngameboy": "Nintendo Game Boy", "nswitch": "Nintendo Switch", "nuuvem": "Nuuvem", "nwii": "Nintendo Wii", "nwiiu": "Nintendo Wii U", "oculus": "Oculus", "origin": "Origin", "paradox": "Paradox Plaza", "pathofexile": "Path of Exile", "pce": "PC Engine", "playasia": "Play-Asia", "playfire": "Playfire", "ps2": "Sony PlayStation 2", "psn": "PlayStation Network", "psp": "PlayStation Portable", "psvita": "PlayStation Vita", "psx": "Sony PlayStation", "riot": "Riot", "rockstar": "Rockstar Games Launcher", "saturn": "SegaSaturn", "sega32": "Sega 32X", "segacd": "Sega CD", "segag": "Sega Genesis", "sms": "Sega Master System", "snes": "SNES", "stadia": "Google Stadia", "star": "Star Citizen", "steam": "Steam", "test": "Test", "totalwar": "Total War", "twitch": "Twitch", "unknown": "Unknown", "uplay": "Uplay", "vision": "ColecoVision", "wargaming": "Wargaming", "weplay": "WePlay", "winstore": "Windows Store", "xboxog": "Original Xbox games", "xboxone": "Xbox Live", "zx": "Zx Spectrum PC" }

conn = sqlite3.connect(database_location)
cursor = conn.cursor()

# gamePieceTypeId is stored in GamePieceTypes
cursor.execute("""SELECT id FROM GamePieceTypes WHERE type = 'originalMeta'""")
originalMetaID = cursor.fetchall()[0][0]
cursor.execute("""SELECT id FROM GamePieceTypes WHERE type = 'meta'""")
metaID = cursor.fetchall()[0][0]
cursor.execute("""SELECT id FROM GamePieceTypes WHERE type = 'originalTitle'""")
originalTitleID = cursor.fetchall()[0][0]
cursor.execute("""SELECT id FROM GamePieceTypes WHERE type = 'title'""")
titleID = cursor.fetchall()[0][0]
# Create a view of OwnedGames joined on GamePieces for a full OwnedGames DB
owned_games_query = """CREATE TEMP VIEW MasterList AS
				SELECT GamePieces.releaseKey, GamePieces.gamePieceTypeId, GamePieces.value FROM OwnedGames
				JOIN GamePieces ON OwnedGames.releaseKey = GamePieces.releaseKey;"""
# Create view of unique items using details
unique_owned_games_query = """CREATE TEMP VIEW UniqueMasterList AS
				SELECT DISTINCT(MasterList.value) AS metadata, MasterCopy.value AS title FROM MasterList, MasterList
				AS MasterCopy WHERE ((MasterList.gamePieceTypeId = {}) OR (MasterList.GamePieceTypeId = {})) AND
				((MasterCopy.gamePieceTypeId = {}) OR (MasterCopy.gamePieceTypeId = {})) AND
				(MasterCopy.releaseKey = MasterList.releaseKey);""".format(originalMetaID, metaID, originalTitleID, titleID)
# Display each game and its details along with corresponding release key grouped by details
aggr_game_data = """SELECT UniqueMasterList.title, GROUP_CONCAT(DISTINCT MasterList.releaseKey), UniqueMasterList.metadata
				FROM UniqueMasterList, MasterList WHERE UniqueMasterList.metadata = MasterList.value
				GROUP BY UniqueMasterList.metadata ORDER BY UniqueMasterList.title;"""
cursor.execute(owned_games_query)
cursor.execute(unique_owned_games_query)
cursor.execute(aggr_game_data)
with open("gameDB.csv", "w", encoding='utf-8', newline='') as csvfile:
	fieldnames = ['title', 'platformList', 'developers', 'publishers', 'releaseDate', 'genres', 'themes', 'criticsScore']
	writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
	writer.writeheader()
	while True:
		result = cursor.fetchone()
		if result:
			# JSON string needs to be converted to dict
			# For json.load() to work correctly, all double quotes must be correctly escaped
			metadata = json.loads(result[2].replace('"','\"'))
			row = metadata
			row['title'] = result[0].split('"')[3]
			row['title'] = row['title'].replace("\\","")
			row['platformList'] = []
			if any(platform in releaseKey for platform in platforms for releaseKey in result[1].split(",")):
				row['platformList'] = set(platforms[platform] for releaseKey in result[1].split(",") for platform in platforms if releaseKey.startswith(platform))
			else:
				row['platformList'].append("Placeholder")
			if metadata['releaseDate']:
				row['releaseDate'] = time.strftime("%Y-%m-%d", time.localtime(metadata['releaseDate']))
			else:
				row['releaseDate'] = metadata['releaseDate']
			if metadata['criticsScore']:
				row['criticsScore'] = round(metadata['criticsScore'])
			else:
				row['criticsScore'] = metadata['criticsScore']
			for key, value in row.items():
				if type(value) == list or type(value) == set:
					row[key] = ",".join(value)
			writer.writerow(row)
		else:
			break
cursor.close()
conn.close()

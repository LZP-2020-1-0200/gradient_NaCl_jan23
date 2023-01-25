import zipfile
import sqlite3
import json
from andor_asc import load_andor_asc
import cnst as c

con = sqlite3.connect(c.DBFILE)
cur = con.cursor()

cur.execute("PRAGMA foreign_keys = ON")

cur.execute(f"DROP TABLE IF EXISTS {c.EXPERIMENTS_TABLE}")
cur.execute(f"""CREATE TABLE IF NOT EXISTS {c.EXPERIMENTS_TABLE}(
    {c.COL_SERIES} TEXT PRIMARY KEY,
    {c.COL_DARK} TEXT,
    {c.COL_DARK_FOR_WHITE} TEXT,
    {c.COL_WHITE} TEXT,
    {c.COL_MEDIUM} TEXT,
    {c.COL_POL} TEXT
    )""")

cur.execute(f"DROP TABLE IF EXISTS {c.SPOTS_TABLE}")
cur.execute(f"""CREATE TABLE IF NOT EXISTS {c.SPOTS_TABLE}(
    {c.COL_SPOT} TEXT PRIMARY KEY,
    {c.COL_XPOS} INTEGER,
    {c.COL_YPOS} INTEGER,
    {c.COL_LINE} INTEGER )""")

cur.execute(f"DROP TABLE IF EXISTS {c.FILE_TABLE}")
cur.execute(f"""CREATE TABLE IF NOT EXISTS {c.FILE_TABLE}(
    {c.COL_MEMBER_FILE_NAME} TEXT PRIMARY KEY,
    {c.COL_FILE_TYPE} TEXT NOT NULL,
    {c.COL_SERIES} TEXT,
    {c.COL_SPOT} TEXT,
    {c.COL_TSTAMP} TEXT,
    FOREIGN KEY ({c.COL_SERIES}) REFERENCES {c.EXPERIMENTS_TABLE} ({c.COL_SERIES}) ,
    FOREIGN KEY ({c.COL_SPOT}) REFERENCES {c.SPOTS_TABLE} ({c.COL_SPOT})
    )""")

ignorelist = ('Pec_kartejuma_caur_stiklu_1802/timestamps.cmd',
              'Pec_kartejuma_caur_stiklu_1802/gaiss_udens_1901_timestamps.txt',
              'Pec_kartejuma_caur_stiklu_1802/Pieraksti.txt'
              )

with zipfile.ZipFile("Pec_kartejuma_caur_stiklu_1802.zip", "r") as spectra_zf:
    for member_file_name in spectra_zf.namelist():
        if member_file_name in ignorelist:
            continue
        if member_file_name[-1] == '/':
            continue
        if 'visi_timestamps' in member_file_name:
            spectra_timestamps_file_name = member_file_name
            continue
        if 'session.json' in member_file_name:
            session_json_file_name = member_file_name
            continue
        if '/refs/white' in member_file_name:
            cur.execute(f"""INSERT INTO {c.FILE_TABLE}
            ({c.COL_MEMBER_FILE_NAME},{c.COL_FILE_TYPE})
            VALUES (?,?)""",
                        [member_file_name, c.WHITE])
            continue
        if '/refs/darkForWhite' in member_file_name:
            cur.execute(f"""INSERT INTO {c.FILE_TABLE}
            ({c.COL_MEMBER_FILE_NAME},{c.COL_FILE_TYPE})
            VALUES (?,?)""",
                        [member_file_name, c.DARK_FOR_WHITE])
            continue
        if '/refs/dark' in member_file_name:
            cur.execute(f"""INSERT INTO {c.FILE_TABLE}
            ({c.COL_MEMBER_FILE_NAME},{c.COL_FILE_TYPE})
            VALUES (?,?)""",
                        [member_file_name, c.DARK])
            continue
        if '.asc' in member_file_name:
            file_name_parts = member_file_name.split('/')
            series = file_name_parts[2]
            cur.execute(f"""INSERT OR IGNORE INTO {c.EXPERIMENTS_TABLE}
            ({c.COL_SERIES}) VALUES (?)""", [series])

            spot = file_name_parts[3]
            # print(spot)
            cur.execute(f"""INSERT OR IGNORE INTO {c.SPOTS_TABLE}
            ({c.COL_SPOT}) VALUES (?)""", [spot])

            cur.execute(f"""INSERT INTO {c.FILE_TABLE}
            ({c.COL_MEMBER_FILE_NAME},{c.COL_FILE_TYPE},{c.COL_SERIES},{c.COL_SPOT})
            VALUES (?,?,?,?)""",
                        [member_file_name, c.SPECTRUM, series, spot])
            continue

    print(session_json_file_name)
    with spectra_zf.open(session_json_file_name) as session_jsf:
        session_json_object = json.load(session_jsf)
    print(session_json_object.keys())
    points = session_json_object['points']
    point_nr = 0
    for point in points:
        #        print(point)
        line = point_nr // 100
#        print(line)
        cur.execute(f"""UPDATE {c.SPOTS_TABLE} SET
            {c.COL_XPOS} = ?,
            {c.COL_YPOS} = ?,
            {c.COL_LINE} = ?
        WHERE {c.COL_SPOT} = ? """,
                    [point['x'], point['y'], line, point['filename']])
        if cur.rowcount != 1:
            print(point)
        point_nr += 1

    with spectra_zf.open(spectra_timestamps_file_name) as spectra_timestamps_file:
        spectra_timestamps_data = spectra_timestamps_file.read()
        timestamps_lines = spectra_timestamps_data.decode('ascii').splitlines()
    for timestamps_line in timestamps_lines:
        #        print (timestamps_line)
        timestamps_line_parts = timestamps_line.split("\t")
        # print(timestamps_line_parts)
        timestamp = timestamps_line_parts[1]
        member_file_name = timestamps_line_parts[0][24:].replace('\\', '/')
        # print(member_file_name)
        cur.execute(f"""UPDATE {c.FILE_TABLE} SET
            {c.COL_TSTAMP} = ?
        WHERE {c.COL_MEMBER_FILE_NAME} = ? """,
                    [timestamp, member_file_name])
        if cur.rowcount != 1:
            print(timestamps_line_parts)
    dark05 = 'Pec_kartejuma_caur_stiklu_1802/refs/dark05.asc'
    dark06 = 'Pec_kartejuma_caur_stiklu_1802/refs/dark06.asc'
    darkForWhite07 = 'Pec_kartejuma_caur_stiklu_1802/refs/darkForWhite07.asc'
    darkForWhite08 = 'Pec_kartejuma_caur_stiklu_1802/refs/darkForWhite08.asc'
    white06 = 'Pec_kartejuma_caur_stiklu_1802/refs/white06.asc'
    white07 = 'Pec_kartejuma_caur_stiklu_1802/refs/white07.asc'

    exp20220119 = [
        [dark05, darkForWhite07, white06, c.AIR, c.S_POL, '006'],
        [dark06, darkForWhite08, white07, c.AIR, c.P_POL, '007'],
        [dark06, darkForWhite08, white07, c.H2O, c.P_POL, '008'],
        [dark06, darkForWhite08, white06, c.H2O, c.S_POL, '009'],
        [dark06, darkForWhite08, white06, c.NaCl_10, c.S_POL, '011'],
        [dark06, darkForWhite08, white07, c.NaCl_10, c.P_POL, '012'],
        [dark06, darkForWhite08, white07, c.NaCl_22, c.P_POL, '013'],
        [dark06, darkForWhite08, white06, c.NaCl_22, c.S_POL, '014']
    ]
    for exp in exp20220119:
        cur.execute(f"""UPDATE {c.EXPERIMENTS_TABLE} SET
            {c.COL_DARK} = ?,
            {c.COL_DARK_FOR_WHITE} = ?,
            {c.COL_WHITE} = ?,
            {c.COL_MEDIUM} = ?,
            {c.COL_POL} = ?
        WHERE {c.COL_SERIES} = ? """,
                    exp)
        if cur.rowcount != 1:
            print(exp)

        for pol in (c.S_POL, c.P_POL):
            print(pol)
            cur.execute(
                f"""SELECT 
                {c.COL_SERIES},
                {c.COL_DARK},
                {c.COL_DARK_FOR_WHITE},
                {c.COL_WHITE},
                {c.COL_MEDIUM}
                FROM {c.EXPERIMENTS_TABLE} WHERE {c.COL_POL} = ?
                ORDER BY {c.COL_SERIES}""", [pol])
            for rez_sel_exp in cur.fetchall():
                print(rez_sel_exp)
                raw_dark = load_andor_asc('', spectra_zf.read(rez_sel_exp[1]))

                


# cur.execute(f"""CREATE TABLE IF NOT EXISTS {c.EXPERIMENTS_TABLE}(
#    {c.COL_SERIES} TEXT PRIMARY KEY,
#    {c.COL_DARK} TEXT,
#    {c.COL_DARK_FOR_WHITE} TEXT,
#    {c.COL_WHITE} TEXT,
#    {c.COL_MEDIUM} TEXT,
#    {c.COL_POL} TEXT
#    )""")


#        lines= data.decode('ascii').splitlines()

#('Pec_kartejuma_caur_stiklu_1802/refs/white06.asc', 'white', None, None)
#('Pec_kartejuma_caur_stiklu_1802/experiments/011/00217.asc', 'spectrum', '011', '00217.asc')
quit()
# print()
#cur.execute(f"""SELECT * from {c.FILE_TABLE}""")
#cur.execute(f"""SELECT * from {c.SPOTS_TABLE}""")
cur.execute(f"""SELECT * from {c.EXPERIMENTS_TABLE}""")
results = cur.fetchall()
for rezult in results:
    print(rezult)

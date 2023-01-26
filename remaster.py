import zipfile
import sqlite3
import json
from andor_asc import load_andor_asc
import cnst as c
from matplotlib import pyplot as plt
import os
import numpy as np
import matplotlib.image as mpimg

OUTFOLDER = 'tmp'

if os.path.exists(OUTFOLDER):
    for f in os.listdir(OUTFOLDER):
        os.remove(os.path.join(OUTFOLDER, f))
else:
    os.mkdir(OUTFOLDER)

ratio = 6/4
width = 7


fig, (axs) = plt.subplots(
    3, figsize=(width, width*ratio))
(ax_dfw, ax_dark, ax_white) = axs

# fig, ((ax_dfw, ax_dark, ax_white)) = plt.subplots(
#    3, figsize=(width, width*ratio))

axx = {c.DARK_FOR_WHITE: ax_dfw, c.DARK: ax_dark, c.WHITE: ax_white}

con = sqlite3.connect(c.DBFILE)
cur = con.cursor()
cur.execute("PRAGMA foreign_keys = ON")

cur.execute(f"DROP TABLE IF EXISTS {c.JPG_FILE_TABLE}")
cur.execute(f"""CREATE TABLE IF NOT EXISTS {c.JPG_FILE_TABLE}(
    {c.COL_JPG_FILE_NAME} TEXT PRIMARY KEY,
    {c.COL_TSTAMP} TEXT UNIQUE NOT NULL
    )""")

with open('pec_kartejuma_caur_stiklu/jpg_timestamps.txt', "r", encoding='utf-8') as jpg_timestamps_fails:
    jpg_timestamp_lines = jpg_timestamps_fails.readlines()
for jpg_timestamp_line in jpg_timestamp_lines:
    jpg_ts_parts = jpg_timestamp_line.strip("\n\r").split("\t")
    # print(jpg_ts_parts)
    if '.jpg' in jpg_ts_parts[0]:
        jpg_filename = jpg_ts_parts[0][3:]
        jpg_ts = jpg_ts_parts[1]
        #print (jpg_filename)
        cur.execute(f"""INSERT INTO {c.JPG_FILE_TABLE}
            ({c.COL_JPG_FILE_NAME},{c.COL_TSTAMP})
            VALUES (?,?)""",
                    [jpg_filename, jpg_ts])
# cur.execute(
#    f"""SELECT * FROM {c.JPG_FILE_TABLE} ORDER BY {c.COL_TSTAMP}""")
# for jpgts_rez in cur.fetchall():
#    print(jpgts_rez)

# quit()


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
    {c.COL_JPG_FILE_NAME} TEXT,
    FOREIGN KEY ({c.COL_SERIES}) REFERENCES {c.EXPERIMENTS_TABLE} ({c.COL_SERIES}) ,
    FOREIGN KEY ({c.COL_SPOT}) REFERENCES {c.SPOTS_TABLE} ({c.COL_SPOT}),
    FOREIGN KEY ({c.COL_JPG_FILE_NAME}) REFERENCES {c.JPG_FILE_TABLE} ({c.COL_JPG_FILE_NAME})
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
    lines = {}
    for point in points:
        #        print(point)
        line = point_nr // 100
        lines[line] = line
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

# insert jpeCOL_TSTAMP
        if 'experiments' in member_file_name:
            #print(f"timestamp = {timestamp}")
            cur.execute(
                f"""SELECT {c.COL_JPG_FILE_NAME}, {c.COL_TSTAMP}
                FROM {c.JPG_FILE_TABLE}
                WHERE {c.COL_TSTAMP} < ?
                ORDER BY {c.COL_TSTAMP} DESC
                LIMIT 1""", [timestamp])
            for rez_jpg_select in cur.fetchall():
                # print(rez_jpg_select)
                cur.execute(f"""UPDATE {c.FILE_TABLE} SET
                    {c.COL_JPG_FILE_NAME} = ?
                WHERE {c.COL_MEMBER_FILE_NAME} = ? """,
                            [rez_jpg_select[0], member_file_name])
                if cur.rowcount != 1:
                    print(rez_jpg_select)

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

    ref_plot_ready = []
    print('XXXXXXXXXX')
    dataset = {}
    for pol in (c.S_POL, c.P_POL):  # ONLY REFERENCES
        dataset[pol] = {}
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
        results_references = cur.fetchall()

        for rez_sel_exp in results_references:
            # print(rez_sel_exp)
            series = rez_sel_exp[0]
            dataset[pol][series] = {}

            dark_zf = rez_sel_exp[1]
            raw_dark = load_andor_asc('', spectra_zf.read(dark_zf))
            dataset[pol][series][c.DARK] = raw_dark['col2']
            if not dark_zf in ref_plot_ready:
                ref_plot_ready.append(dark_zf)
                ax_dark.plot(
                    raw_dark['col1'], raw_dark['col2'], label=f"{pol} {dark_zf}")
            dfw_zf = rez_sel_exp[2]
            raw_dfw = load_andor_asc('', spectra_zf.read(dfw_zf))
            dataset[pol][series][c.DARK_FOR_WHITE] = raw_dfw['col2']

            if not dfw_zf in ref_plot_ready:
                ref_plot_ready.append(dfw_zf)
                ax_dfw.plot(raw_dfw['col1'], raw_dfw['col2'],
                            label=f"{pol} {dfw_zf}")
            white_zf = rez_sel_exp[3]
            raw_white = load_andor_asc('', spectra_zf.read(white_zf))
            dataset[pol][series][c.WHITE] = raw_white['col2']

            if not white_zf in ref_plot_ready:
                ref_plot_ready.append(white_zf)
                ax_white.plot(
                    raw_white['col1'], raw_white['col2'], label=f"{pol} {white_zf}")
    nm = raw_white['col1']
    dataset[c.NM] = nm
    print(ref_plot_ready)
    for ax in axs:
        ax.set(xlabel='$\\lambda$, nm')
        ax.set(ylabel='counts')
        ax.set(xlim=[min(nm), max(nm)])
        ax.legend(loc="best")
        ax.grid()

    ax_dfw.title.set_text(c.DARK_FOR_WHITE)
    ax_dark.title.set_text(c.DARK)
    ax_white.title.set_text(c.WHITE)
    plt.tight_layout()
    plt.savefig(f"{OUTFOLDER}/references.png", dpi=300)
    plt.close()
    # print(dataset)

    frame = 1000000000
    for pol in (c.S_POL, c.P_POL):  # Start processing
        for line in lines.keys():
            cur.execute(
                f"""SELECT
                {c.COL_SPOT},
                {c.COL_XPOS},
                {c.COL_YPOS}
                FROM {c.SPOTS_TABLE}
                WHERE  {c.COL_LINE} = ?
                ORDER BY {c.COL_SPOT}
                LIMIT 9999""",
                [line])

            for spot_rez in cur.fetchall():
                spot = spot_rez[0]
                xpos = spot_rez[1]
                ypos = spot_rez[2]

                print(spot)
                cur.execute(
                    f"""SELECT
                    {c.EXPERIMENTS_TABLE}.{c.COL_SERIES},
                    {c.FILE_TABLE}.{c.COL_MEMBER_FILE_NAME},
                    {c.EXPERIMENTS_TABLE}.{c.COL_MEDIUM},
                    {c.FILE_TABLE}.{c.COL_JPG_FILE_NAME}
                    FROM {c.EXPERIMENTS_TABLE}
                    INNER JOIN {c.FILE_TABLE} ON {c.FILE_TABLE}.{c.COL_SERIES}={c.EXPERIMENTS_TABLE}.{c.COL_SERIES}
                    WHERE {c.EXPERIMENTS_TABLE}.{c.COL_POL} =?
                    AND {c.FILE_TABLE}.{c.COL_SPOT} = ?
                    """,
                    [pol, spot])

                fig = plt.figure()
                fig.set_figheight(9)
                fig.set_figwidth(16)

                ax1 = plt.subplot2grid(
                    shape=(4, 4), loc=(0, 0), colspan=3, rowspan=4)
                ax2 = plt.subplot2grid(shape=(4, 4), loc=(0, 3))
                ax3 = plt.subplot2grid(shape=(4, 4), loc=(1, 3))
                ax4 = plt.subplot2grid((4, 4), (2, 3))
                ax5 = plt.subplot2grid((4, 4), (3, 3))

                axbmp = [ax2, ax3, ax4, ax5]
                bmp_n = 0
                for ser_rez in cur.fetchall():
                    print(ser_rez)
                    series = ser_rez[0]
                    medium = ser_rez[2]
                    jpg_file_name = ser_rez[3]
                    print(jpg_file_name)
                    img = mpimg.imread(jpg_file_name)
                    axbmp[bmp_n].imshow(img)
                    axbmp[bmp_n].axis('off')
                    axbmp[bmp_n].set_title(medium)

                    dfw = np.array(dataset[pol][series][c.DARK_FOR_WHITE])
                    white = np.array(dataset[pol][series][c.WHITE])
                    ref = white-dfw
                    dark = np.array(dataset[pol][series][c.DARK])
                    raw_spec = load_andor_asc('', spectra_zf.read(ser_rez[1]))

                    counts = np.array(raw_spec['col2'])
                    Q = np.divide(counts-dark, ref)

                    ax1.plot(nm, Q, label=medium)
                    bmp_n += 1

                ax1.set_title(
                    f"{pol}, {spot}, line={line}, xpos={xpos}, ypos={ypos}")
                ax1.set(xlabel='$\\lambda$, nm')
                ax1.set(ylabel='counts')

                ax1.set_xlim([min(nm), max(nm)])
                if pol == c.P_POL:
                    ax1.set_ylim([0, 0.5])
                else:
                    ax1.set_ylim([0, 1.0])

                ax1.legend(loc='upper left')
                ax1.grid()
#                plt.savefig(
#                    f"{OUTFOLDER}{exp_key}-{point['filename'].replace('.asc','.png')}", dpi=300)
                plt.tight_layout()
                plt.savefig(
                    f"{OUTFOLDER}/frame{frame}.png", dpi=300)
                plt.close()
                frame += 1


# cur.execute(f"""CREATE TABLE IF NOT EXISTS {c.FILE_TABLE}(
#    {c.COL_MEMBER_FILE_NAME} TEXT PRIMARY KEY,
#    {c.COL_FILE_TYPE} TEXT NOT NULL,
#    {c.COL_SERIES} TEXT,
#    {c.COL_SPOT} TEXT,
#    {c.COL_TSTAMP} TEXT,


#            for series in dataset[pol].keys():
#                print(series)
#                nm = np.array(dataset[c.NM])
#                dfw = np.array(dataset[pol][series][c.DARK_FOR_WHITE])
#                white = np.array(dataset[pol][series][c.WHITE])
#                ref = white-dfw
#                dark = np.array(dataset[pol][series][c.DARK])

    dataset_json_object = json.dumps(dataset)
    with open(f"{OUTFOLDER}/dataset.json", "w") as outfile:
        outfile.write(dataset_json_object)


# cur.execute(f"""CREATE TABLE IF NOT EXISTS {c.EXPERIMENTS_TABLE}(
#    {c.COL_SERIES} TEXT PRIMARY KEY,
#    {c.COL_DARK} TEXT,
#    {c.COL_DARK_FOR_WHITE} TEXT,
#    {c.COL_WHITE} TEXT,
#    {c.COL_MEDIUM} TEXT,
#    {c.COL_POL} TEXT
#    )""")


#        lines= data.decode('ascii').splitlines()

# ('Pec_kartejuma_caur_stiklu_1802/refs/white06.asc', 'white', None, None)
# ('Pec_kartejuma_caur_stiklu_1802/experiments/011/00217.asc', 'spectrum', '011', '00217.asc')
quit()
# print()
# cur.execute(f"""SELECT * from {c.FILE_TABLE}""")
# cur.execute(f"""SELECT * from {c.SPOTS_TABLE}""")
cur.execute(f"""SELECT * from {c.EXPERIMENTS_TABLE}""")
results = cur.fetchall()
for rezult in results:
    print(rezult)

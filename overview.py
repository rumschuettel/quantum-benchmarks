#!/usr/bin/env python

import sys, re
import pandas as pd

from pathlib import Path

RUN_FOLDER_BASE = "./runs" if len(sys.argv) == 1 else sys.argv[1]

table = pd.DataFrame(columns=["mode", "vendor", "device", "benchmark", "date"])

for path in Path(RUN_FOLDER_BASE).rglob("visualize.pdf"):
    if "obsolete" in path.parts:
        continue

    folder = path.parent
    run_folder, run = "/".join(path.parts[:-2]), path.parts[-2]

    try:
        mode = list(Path(folder).glob("*.mode"))[0].stem
        vendor = list(Path(folder).glob("*.vendor"))[0].stem
        device = list(Path(folder).glob("*.device"))[0].stem
        benchmark = list(Path(folder).glob("*.benchmark"))[0].stem
        date = re.search("\d\d\d\d-\d\d-\d\d", run).group()
    except:
        print("ERROR", folder)
        continue

    # stemming for sub-lattices
    if device[:5] == "Aspen":
        device = device[:7]

    table = table.append(
        {
            "mode": mode,
            "vendor": vendor,
            "device": device,
            "benchmark": benchmark,
            "date": date,
        },
        ignore_index=True,
    )

for mode in set(table["mode"]):
    print(mode)
    _table = table[table["mode"] == mode].drop(["mode", "vendor"], axis="columns")
    print(
        _table.groupby(["device", "benchmark"]).aggregate(
            lambda tdf: tdf.unique().tolist()
        )
    )

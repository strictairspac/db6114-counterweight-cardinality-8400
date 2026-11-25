"""校准样本联合统计的存取格式。

统计随资料版本一起发布：重算结果先写入版本行，发布指针切换后新统计才生效。
"""


def pack(frequencies):
    cells = [
        {"mass": mass, "slot": slot, "count": count}
        for (mass, slot), count in sorted(frequencies.items())
    ]
    return {"population": sum(frequencies.values()), "cells": cells}


def unpack(stats):
    if not isinstance(stats, dict) or not isinstance(stats.get("cells"), list):
        raise ValueError("校准统计缺失，请等待重算完成")
    frequencies = {}
    for cell in stats["cells"]:
        frequencies[(cell["mass"], cell["slot"])] = cell["count"]
    if not frequencies:
        raise ValueError("校准统计缺失，请等待重算完成")
    return frequencies

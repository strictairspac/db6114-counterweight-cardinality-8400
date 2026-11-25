CELLS = [("轻档", "紧槽"), ("轻档", "宽槽"), ("重档", "紧槽"), ("重档", "宽槽")]
CHECKS = [
    {"code": f"FL-2411-{index:02}", "mass": mass, "slot": slot}
    for index, (mass, slot) in enumerate(CELLS, 1)
]


def lots(calibration, inspection):
    return {
        "calibration": [
            {"mass": mass, "slot": slot, "count": count}
            for (mass, slot), count in zip(CELLS, calibration)
        ],
        "inspection": [
            {"mass": mass, "slot": slot, "count": count}
            for (mass, slot), count in zip(CELLS, inspection)
        ],
        "checks": CHECKS,
    }


FIXTURES = [
    {
        "code": "FL-2411-MIX",
        "title": "货梯配重加严抽查",
        "description": "同供应线两项公差随工装成对偏移，估算复检会取到多少检测记录。",
        "payload": lots([45, 5, 5, 45], [54, 6, 6, 54]),
    },
    {
        "code": "FL-2411-DRIFT",
        "title": "临时工装配对漂移",
        "description": "校准沿用原供应线，待查批次换了临时工装，检测证据应暴露统计失配。",
        "payload": lots([45, 5, 5, 45], [6, 54, 54, 6]),
    },
]

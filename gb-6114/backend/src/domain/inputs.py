from dataclasses import dataclass


@dataclass(frozen=True)
class Cell:
    mass: str
    slot: str
    count: int


@dataclass(frozen=True)
class Check:
    code: str
    mass: str
    slot: str


def label(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 24 or value != value.strip():
        raise ValueError("档位和复检号须为 1 到 24 字、首尾无空格")
    if any(ord(char) < 32 or 0xD800 <= ord(char) <= 0xDFFF for char in value):
        raise ValueError("档位和复检号不可包含控制字符或孤立代理字符")
    return value


def cells(items, section):
    if not isinstance(items, list) or not 1 <= len(items) <= 64:
        raise ValueError(f"{section}须为 1 到 64 个单元")
    parsed = []
    for item in items:
        if not isinstance(item, dict) or set(item) != {"mass", "slot", "count"}:
            raise ValueError(f"{section}单元需要 mass、slot、count 字段")
        mass, slot, count = label(item["mass"]), label(item["slot"]), item["count"]
        if type(count) is not int or not 1 <= count <= 1000:
            raise ValueError("单元件数须为 1 到 1000 的整数")
        parsed.append(Cell(mass, slot, count))
    if len({(item.mass, item.slot) for item in parsed}) != len(parsed):
        raise ValueError(f"{section}的组合档位重复")
    if sum(item.count for item in parsed) > 2400:
        raise ValueError(f"{section}的检测总数超过 2400")
    return parsed


def parse(payload):
    if not isinstance(payload, dict):
        raise ValueError("请输入复检对象")
    calibration = cells(payload.get("calibration"), "校准批次")
    inspection = cells(payload.get("inspection"), "待查批次")
    items = payload.get("checks")
    if not isinstance(items, list) or not 1 <= len(items) <= 64:
        raise ValueError("输入 1 到 64 个复检组合")
    checks = []
    for item in items:
        if not isinstance(item, dict) or set(item) != {"code", "mass", "slot"}:
            raise ValueError("复检组合需要 code、mass、slot 字段")
        checks.append(Check(label(item["code"]), label(item["mass"]), label(item["slot"])))
    if len({item.code for item in checks}) != len(checks):
        raise ValueError("复检号重复")
    return calibration, inspection, checks

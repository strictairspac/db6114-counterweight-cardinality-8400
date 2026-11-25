from statistics import mean

from .estimates import JointEstimator, q_error
from .fixtures import FIXTURES
from .inputs import parse
from .lot_table import actual_count, inspection_table, joint_frequencies


CONFIG = {
    "title": "铅绳梯检·货梯配重检索估算",
    "team": "铅绳梯检 11 人来料测量与井道复核组",
    "description": "用已校准批次预估组合公差复检清单的大小，拿待查库的真实结果校核单列估算与联合高频项。",
    "direction": "查询基数与相关列统计",
    "mechanism": "比较独立性基线和联合 MCV 估算，用真实 MySQL 双条件查询验核。",
    "modules": ["配重工装台", "批次与复检条件", "基数估算", "复检容量证明"],
    "unit": "检测批次",
    "max_parameter": 64,
    "default_parameter": 2,
    "parameter_label": "联合统计保留的档位对",
    "facts": ["双档位", "独立性估算", "联合高频项"],
    "palette": 14,
    "fixture": "counterweights-2411-calibration.json",
}


def validate(payload):
    parse(payload)


def run(payload, parameter, db):
    calibration, inspection, checks = parse(payload)
    inspection_size = sum(cell.count for cell in inspection)
    rows = []
    base_errors = []
    joint_errors = []
    with inspection_table(db, calibration, inspection) as table:
        estimator = JointEstimator(joint_frequencies(db, table), parameter)
        for check in checks:
            independent = float(inspection_size * estimator.independent(check.mass, check.slot))
            joint = float(inspection_size * estimator.joint(check.mass, check.slot))
            actual = actual_count(db, table, check)
            base_errors.append(q_error(independent, actual))
            joint_errors.append(q_error(joint, actual))
            rows.append({
                "复检号": check.code,
                "重量档": check.mass,
                "槽宽档": check.slot,
                "独立估算": round(independent, 2),
                "联合估算": round(joint, 2),
                "数据库实测": actual,
                "独立 Q-error": round(base_errors[-1], 3),
                "联合 Q-error": round(joint_errors[-1], 3),
            })
    base_mean, joint_mean = round(mean(base_errors), 3), round(mean(joint_errors), 3)
    return {
        "summary": f"已核验 {len(checks)} 条双条件查询。平均 Q-error 从 {base_mean:g} 变为 {joint_mean:g}，最优值为 1。",
        "metrics": {"实测查询": len(rows), "独立平均误差": base_mean, "联合平均误差": joint_mean},
        "rows": rows,
    }

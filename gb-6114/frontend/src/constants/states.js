export const States = Object.freeze({
  queued: "等待执行", done: "已完成", failed: "执行失败",
  computing: "重算中", ready: "已就绪",
});

export const RevisionStates = Object.freeze({
  computing: "统计重算中", ready: "已就绪", failed: "重算失败",
});

export const Actions = Object.freeze({
  create_case: "登记资料", correct_case: "提交更正", enqueue: "提交执行",
  done: "执行完成", failed: "执行失败", review: "复核签署",
  recalc_ready: "统计就绪", recalc_failed: "重算失败",
});

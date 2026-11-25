import { api } from "../api/workbench.js";
import { errorText, field } from "../components/common/fields.js";
import { empty, pageHeading, section } from "../components/common/panel.js";
import { table } from "../components/common/table.js";
import { RevisionStates } from "../constants/states.js";
import { poll } from "../hooks/poll.js";
import { submit } from "../hooks/submit.js";
import { navigate } from "../router/router.js";
import { el } from "../utils/dom.js";
import { time } from "../utils/format.js";

function refresh() {
  window.dispatchEvent(new Event("hashchange"));
}

function stateChip(state) {
  return el("span", {class: `status state-${state}`, "data-state": state}, RevisionStates[state] || state);
}

function queueForm(config, selected) {
  const form = el("form", {class: "queue-form"},
    field(config.parameter_label, el("input", {
      name: "parameter", type: "number", min: 1, max: config.max_parameter, required: true, value: config.default_parameter,
    }), `接单时锁定已发布 v${selected.current_version} 的样本与统计`),
    el("button", {type: "submit"}, "提交执行"), errorText());
  submit(form, async values => {
    const run = await api.enqueue(selected.id, {parameter: Number(values.get("parameter"))});
    navigate(`runs/${run.id}`);
  });
  return form;
}

function versionNotes(selected) {
  const notes = [el("p", {}, `已发布 v${selected.current_version} · 最新提交 v${selected.latest_version}`)];
  if (selected.latest_status === "computing") {
    notes.push(el("p", {}, "统计重算中，期间接单与排队批次仍按已发布版本出结果。"));
  } else if (selected.latest_status === "failed") {
    notes.push(el("p", {class: "feedback", role: "alert"},
      `最新更正重算失败：${selected.latest_failure || "请检查 worker 日志"} 已发布版本不受影响，可基于最新提交修正后重新更正。`));
  }
  return el("div", {class: "stack"}, notes);
}

function correction(selected) {
  const form = el("form", {id: "correction-form"},
    field("校准样本内容", el("textarea", {name: "payload", spellcheck: "false", required: true, rows: 12},
      JSON.stringify(selected.payload, null, 2)),
      `基于最新提交 v${selected.latest_version} 更正；提交后后台重算统计，就绪后与样本一次性切换发布。`),
    errorText(), el("button", {type: "submit"}, "提交更正"));
  submit(form, async values => {
    let payload;
    try {
      payload = JSON.parse(values.get("payload"));
    } catch {
      throw new Error("资料 JSON 无法解析，请检查括号、引号和逗号");
    }
    await api.correctCase(selected.id, {payload, base_version: selected.latest_version});
    refresh();
  });
  return form;
}

function registration(config, selected) {
  const data = selected ? JSON.stringify(selected.payload, null, 2) : "{}";
  const form = el("form", {id: "case-form"},
    field("名称", el("input", {name: "title", required: true, minlength: 2, maxlength: 120, value: selected ? `${selected.title} · 复演` : ""})),
    field("说明", el("input", {name: "description", maxlength: 420, value: selected?.description || ""})),
    field(`${config.unit}内容`, el("textarea", {name: "payload", spellcheck: "false", required: true, rows: 12}, data),
      selected ? "可以保留演示数据，也可以编辑 JSON 后保存。" : "输入业务 JSON。"),
    errorText(), el("button", {type: "submit"}, "保存资料"));
  submit(form, async values => {
    let payload;
    try {
      payload = JSON.parse(values.get("payload"));
    } catch {
      throw new Error("资料 JSON 无法解析，请检查括号、引号和逗号");
    }
    const entry = await api.createCase({title: values.get("title"), description: values.get("description"), payload});
    navigate(`cases/${entry.id}`);
  });
  return form;
}

function revisionHistory(items) {
  return table(["版本", "状态", "基于", "提交人", "提交时间", "完成时间"], items.map(item => [
    `v${item.version}`,
    el("span", {class: "stack"}, stateChip(item.status), item.failure ? el("small", {class: "feedback"}, item.failure) : null),
    item.base_version ? `v${item.base_version}` : "—",
    item.actor, time(item.created_at), time(item.finished_at),
  ]), "版本记录");
}

function watchRecalculation(selected, signal) {
  if (selected?.latest_status !== "computing" || !signal) return;
  poll(async () => {
    try {
      const next = await api.caseDetail(selected.id, signal);
      if (signal.aborted) return false;
      if (next.latest_status === "computing") return true;
      refresh();
    } catch {
      // 轮询失败时停止，页面仍展示已获取的状态。
    }
    return false;
  }, signal, 1200);
}

export async function casesPage(config, user, route, signal) {
  const cases = await api.cases();
  const picked = cases.find(item => item.id === route.id) ?? cases.at(-1);
  const selected = picked ? await api.caseDetail(picked.id, signal) : null;
  const revisions = selected ? await api.revisions(selected.id) : [];
  const operator = user.role === "operator";
  watchRecalculation(selected, signal);
  return el("div", {class: "page"},
    pageHeading(config.modules[1], `${config.unit} · ${config.fixture}`),
    section("资料目录", cases.length ? table(["编号", "名称", "已发布", "最新提交", "说明", "操作"], cases.map(item => [
      item.code, item.title, `v${item.current_version}`,
      item.latest_version > item.current_version || item.latest_status !== "ready"
        ? el("span", {}, `v${item.latest_version} `, stateChip(item.latest_status)) : "—",
      item.description,
      el("a", {href: `#cases/${item.id}`, "aria-current": item.id === selected?.id ? "true" : null}, "选用"),
    ]), "资料目录") : empty("这里还没有资料。")),
    el("div", {class: "split case-split"},
      section(selected ? selected.title : "等待选择资料", selected ?
        [el("p", {}, selected.description), versionNotes(selected),
          operator ? queueForm(config, selected) : empty("当前账号可查看此资料。"),
          el("details", {}, el("summary", {}, "查看最新提交的业务数据"), el("pre", {}, JSON.stringify(selected.payload, null, 2)))] :
        empty("先登记一条资料，再提交执行。")),
      operator ? el("div", {class: "stack"},
        section("更正校准样本", selected ? correction(selected) : empty("先选用一条资料。")),
        section("登记新资料", registration(config, selected))) : null),
    selected ? section("版本记录", revisions.length ? revisionHistory(revisions) : empty("暂无版本记录。")) : null);
}

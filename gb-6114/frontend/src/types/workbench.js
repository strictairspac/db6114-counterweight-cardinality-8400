/**
 * @typedef {{id:number, code:string, title:string, description:string, created_by:string,
 *   current_version:number, latest_version:number, latest_status:string}} CaseSummary
 * @typedef {CaseSummary & {payload:Object, latest_failure:string|null}} CaseDetail
 * @typedef {{id:number, case_id:number, version:number, status:string, base_version:number|null,
 *   actor:string, failure:string|null, created_at:number, finished_at:number|null}} Revision
 * @typedef {{id:number, case_id:number, case_version:number|null, case_title:string, status:string,
 *   parameter:number, result:Object|null}} Run
 * @typedef {{run_id:number, actor:string, note:string, created_at:number}} Review
 */

/** Reject a malformed configuration before rendering its navigation. */
export function validateConfig(config) {
  if (!config || !Array.isArray(config.modules) || config.modules.length !== 4 ||
      !Number.isInteger(config.default_parameter) || !config.title) {
    throw new Error("工作台配置不完整");
  }
  return config;
}

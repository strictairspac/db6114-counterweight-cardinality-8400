# 铅绳梯检·货梯配重检索估算

用已校准批次预估组合公差复检清单的大小，拿待查库的真实结果校核单列估算与联合高频项。

## 业务流程

1. 配重工装台
2. 批次与复检条件
3. 基数估算
4. 复检容量证明

比较独立性基线和联合 MCV 估算，用真实 MySQL 双条件查询验核。

测量组原先把重量档和槽宽档各自命中比例相乘。遇成对偏移时会把稀有组合算多、把常见组合算少，更换工装后又容易沿用过期统计。上游是供货样本和待查检测记录，下游是复检组分 2 个工位排查。

08:15 打开 counterweights-2411-calibration.json 对应的配重加严卷。08:18 核对 100 条校准、120 条待查。08:20 选择四个组合留作复检。08:25 设置保留 2 个高频项。08:28 对比实际 54、6、6、54 条。08:31 复核联合 Q-error 平均 1。08:40 换临时工装批次核实失配并导出交接。

独立估算用待查总数乘校准样本两个边际概率。联合估算照录前 k 个组合频率，剩余概率质量按未入榜组合的相对边际乘积分配。排序同频按标签打破平局，估算用未舍入运算，Q-error 的零值按 1 平滑。真实 MySQL 临时表装载两个批次的独立明细，COUNT 验核每个组合。域外档位在模型中归为零估算，待查有值则会体现误差；统计失配可能使联合方法更差。

这是可解释的应用基数模型，有关结果用于人工估算复检容量。不会修改 MySQL 优化器统计。

## 启动

```sh
cp -n .env.example .env
docker compose config --quiet
docker compose up -d --build --wait
```

打开 <http://localhost:18315>。OpenAPI 在 <http://localhost:19315/docs>，数据库映射到本机 17815。所有暴露端口只绑定回环地址。Compose 启动 frontend、backend、worker、db、redis，各自通过健康探针检查。数据库、Redis 和共享产物目录各有命名卷；任务状态及导出内容以数据库中的证据为准。

首次启动时幂等载入演示数据。手动载入可运行 `docker compose exec -T backend python -m scripts.seed_demo`。常规停止可用 `docker compose down`。验收环境清理才加 `-v`，它会删除本项目的数据卷。

## 角色与交接

演示账号共用口令 `Demo-DbWorkbench-2026`。

| 登录名 | 角色 | 可执行操作 |
|---|---|---|
| operator | 资料操作员 | 登记业务资料、设置「联合统计保留的档位对」、提交、查看和下载结果 |
| reviewer | 业务复核员 | 查看执行证据、签署单次复核、下载交接单 |
| viewer | 只读观察员 | 查看资料、执行结果及审计，下载证据 |

选用「counterweights-2411-calibration.json」对应的演示资料，保存一份复演资料，再以默认参数 2 提交。worker 保存结果摘要、业务明细和 SHA-256。复核员登录后在「复检容量证明」签署。

## 开发说明

| 部分 | 实现 |
|---|---|
| 前端 | 原生 HTML、CSS、JavaScript ES Modules、Nginx |
| 后端 | Python 3.11、FastAPI、SQLAlchemy、JWT |
| 数据库 | MySQL 8.0 |
| 后台执行 | Redis 通知、数据库持久任务队列和行锁、Python worker |

从 `backend/src/domain/scenario.py` 修改业务入口和演示口径，运行 `docker compose up -d --build --wait` 查看变更。数据库表结构在 `backend/src/models` 和 `backend/migrations`，输入模型在 `backend/src/schemas`。业务页和请求接口在 `frontend/src/pages`、`frontend/src/api`。资料、执行、复核三个工作流实体各有独立表和 API；场景输入及结果保留在所属资料和批次中。

角色枚举在 `backend/src/constants/roles.py`、`frontend/src/constants/roles.js`，用于服务端访问控制、账号初始化、前端导航与签署。批次状态在 `backend/src/constants/job_state.py`、`frontend/src/constants/states.js`，用于队列、状态 API、状态标记与轮询。登记、提交、完成和签署事件写入审计表。

`COMPOSE_PROJECT_NAME` 设置栈名，`FRONTEND_PORT`、`BACKEND_PORT`、`DB_PORT` 设置端口。通过 `DB_PASSWORD`、`JWT_SECRET`、`DEMO_PASSWORD` 配置本地凭据。设置 `SEED_DEMO=false` 可关闭演示数据载入，此时数据库初始没有演示账号。数据库密码调整后，已有数据卷需在数据库内同步修改用户密码。

## 验收范围

估算针对样本关联列。联合频数来自校准批，漂移样本可表现出高于独立基线的误差。 当前界面用 JSON 编辑业务资料，以 JSON 下载证据。过程和截图保存在批次的 [验收记录](../../test-artifacts/gb-6114/TESTING.md)。

[MIT License](LICENSE)

---
name: github-image-workflow-builder
description: 创建、修复和验证项目级 GitHub Actions 镜像构建 Workflow，适用于 amd64/arm64 分开构建、可选镜像推送、Release 打包和 Webhook 通知。
metadata:
  short-description: 严谨构建和排障 GitHub 镜像 Workflow
---

# GitHub Image Workflow Builder

## 目标

为当前项目创建一套可直接运行、可手动触发、可解释失败原因的 GitHub Actions 镜像 Workflow。默认按 amd64 和 arm64 分成两个矩阵任务，并使用对应架构的 Runner；除非用户明确要求，不创建统一的多架构 manifest。

该 Skill 面向“项目内自包含”的 Workflow：不要默认引入外部共享 Workflow、Reusable Workflow 或公共配置仓库。CI 辅助脚本应放在项目的 `.github/image-make/`，不要污染已有的业务 `scripts/` 目录。

三种运行模式必须保持语义一致：`build-only` 构建并打包创建 Release（默认不推送阿里云），`build-and-release` 构建、按配置推送阿里云并创建 Release，`release-only` 不构建而从已有阿里云镜像拉取后创建 Release。

## 何时使用

用户要求以下任一项时使用：

- 创建或修复 GitHub 镜像构建 Workflow
- 分开构建 amd64 和 arm64 镜像
- 使用原生 arm64 Runner，例如 `ubuntu-24.04-arm`
- 将镜像保存为 Release 附件
- 可选推送到阿里云或其他镜像仓库
- 可选调用 HAP Webhook
- 排查 buildx、架构不匹配、Job skipped、Artifact、Release 或 Workflow Summary 问题

不适用于单纯 Dockerfile 编写、普通业务脚本或只要求发布已有镜像而不涉及 GitHub Workflow 的任务。

## 必须遵守的设计

1. 先扫描项目：读取现有 Dockerfile、`.github/workflows/`、`.image-build.env`、`scripts/`、README 和 Git 状态；保留用户已有改动。
2. 架构分开构建：
   - amd64 使用 `linux/amd64` 和 `ubuntu-24.04`
   - arm64 使用 `linux/arm64` 和 `ubuntu-24.04-arm`
   - 不在 amd64 Runner 上用 QEMU 代替原生 arm64，除非用户明确要求
3. 基础镜像按架构独立配置：`BASE_IMAGE_AMD64` 和 `BASE_IMAGE_ARM64` 可以完全不同，不能通过字符串替换猜测 arm64 镜像。
4. Dockerfile 保持手动可构建：默认值应允许 `docker build .` 在当前平台工作；CI 通过 `--build-arg BASE_IMAGE=...` 覆盖架构基础镜像。
5. 主镜像名只作为本地 Build、Save 和 Release 中的镜像引用：不为主镜像名登录或推送，除非用户明确要求主仓库 Push。
6. 阿里云 Push 是独立可选模块：只有地址、命名空间和账号密码齐全时执行 `docker tag` 与 `docker push`；缺少配置时跳过 Push，但不能阻断 Build 或使用主镜像生成 Release。
7. Release 选择镜像来源：有阿里云 Push 时优先从阿里云镜像打包；没有阿里云配置时使用构建出的本地镜像 Artifact。Release-only 模式无法访问本地 Build 时，必须明确要求可拉取的阿里云镜像，或先执行 Build。
8. HAP Webhook 必须使用 nginx-make 兼容的通用 JSON 协议：固定输出 `project_name`、`repository`、`version`、`tag`、`release_url`、`amd64_name`、`amd64_url`、`amd64_sha256`、`arm64_name`、`arm64_url`、`arm64_sha256`、`attachment_urls`、`commit_sha`、`run_id`、`run_url`、`build_status`；其中 `attachment_urls` 是 JSON 字符串，不是 JSON 数组。项目名从 `RELEASE_NAME` 或仓库名推导，不能把项目字段硬编码到 CI 引擎。
9. HAP Webhook URL 为空或开关关闭时只跳过通知，并在 `$GITHUB_STEP_SUMMARY` 写出明确原因；不能因为 URL 为空而让 Release 失败。通知只在 Release 成功后发送。
10. 每个独立 Job 都必须 checkout 仓库。Job 之间只共享 Artifact 和 Job Outputs，不共享工作区文件。
11. 不要使用保留环境变量名作为业务配置名。尤其不要把构建目录命名为 `DOCKER_CONTEXT`；Docker 会将其解释为 Docker Context 名称。使用 `BUILD_CONTEXT`。
12. buildx 必须可靠初始化。不要依赖空的 `BUILDX_BUILDER` 或某个 Action 的隐式 Builder；构建脚本应明确选择或创建 Builder，并在构建时传 `--builder`。
13. Artifact 名称按镜像最后一段和 tag 生成，例如：

   ```text
   hap-promtail-vlogs-mongodb-amd64:1.0.0
   -> hap-promtail-vlogs-mongodb-amd64_1.0.0.tar.gz
   ```
14. Actions UI 步骤保持精简：推荐每个构建 Job 只保留 checkout、一个包含登录/Builder/Build/Push/Save 的构建步骤和 Artifact 上传；不要为每个正常动作拆出大量可视步骤。失败原因写入日志和 Summary 即可。
15. Alpine 源和版本应可配置：使用 `ALPINE_MIRROR`、`ALPINE_VERSION`，不要把源地址散落在多个文件中；删除 `apk update` 与 `apk add --no-cache` 的重复索引刷新。
16. 所有自有 CI 脚本的成功日志都应参考 nginx-make 收敛：输出阶段标题、`[INFO]`、`[OK]` 和最终结果；Docker/BuildKit、Push、Pull 详细日志写入临时日志文件，失败时输出末尾足够定位问题的内容。第三方 Action 的系统日志不强行重写。
17. Workflow 本身不得写入具体项目的镜像仓库、namespace 或 Release 名。项目个性化值放入 `.image-build.env`；未配置时使用仓库名推导 Release 名，镜像模块应明确跳过并说明原因。
18. 如果项目内存在 Skill、文档或其他非构建目录，Workflow 的 push 触发器应通过 `paths-ignore` 排除这些目录；Skill 变更不应触发镜像构建，但仍应支持手动触发验证。

## 推荐目录

```text
.github/
├── workflows/image-make.yml       # 触发器、Job、矩阵、权限和依赖
└── image-make/
    ├── config.py                   # 配置合并、模块判断、Summary
    ├── build.sh                    # 单架构 Build、Tag、Push、Save
    ├── package.sh                  # Artifact 校验或 Release-only 打包
    └── release.py                  # manifest、下载链接和 Release Summary
```

不要把这些 CI 脚本放入项目已有的 `scripts/`，除非该目录本来就是专门的 CI 工具目录。

## 配置和优先级

优先级必须在 README、Workflow Summary 和实现中保持一致。推荐：

```text
workflow_dispatch 输入
> GitHub Repository Variables
> .image-build.env
> Workflow 默认值
```

建议配置项：

```text
IMAGE_TAG
RELEASE_NAME
BASE_IMAGE_AMD64
BASE_IMAGE_ARM64
TARGET_IMAGE_AMD64
TARGET_IMAGE_ARM64
ALIYUN_REGISTRY
ALIYUN_NAMESPACE
ALIYUN_IMAGE_AMD64
ALIYUN_IMAGE_ARM64
ALPINE_MIRROR
ALPINE_VERSION
ENABLE_BUILD
ENABLE_ALIYUN_PUSH
ENABLE_RELEASE
ENABLE_HAP_WEBHOOK
DOCKERFILE
BUILD_CONTEXT
```

账号、密码、Webhook URL、签名只能来自 GitHub Actions Secrets，不得写入仓库配置文件。

GitHub 配置入口统一为 `Settings → Secrets and variables → Actions`：非敏感项放 `Variables`，账号密码、Webhook URL、AppKey 和 Sign 放 `Secrets`。HAP 至少需要 `HAP_WEBHOOK_URL` 和 `ENABLE_HAP_WEBHOOK=true`；`HAP_WEBHOOK_APP_KEY`、`HAP_WEBHOOK_SIGN` 按接收端要求配置。配置后必须通过 `Actions → Image Make → Run workflow` 手动验证，并检查 config/Release Summary 的启用、跳过原因和 HAP 请求结果。

README 必须区分三类默认值：手动 `workflow_dispatch` 输入默认值、项目 `.image-build.env` 默认值，以及没有默认值的必填配置。通用 Workflow 不得伪造项目镜像名；镜像地址、namespace 等未配置时必须写明“无默认值”和实际跳过行为。

## 通用性审计

完成后必须对 Workflow 和 CI 脚本做一次项目脱敏检查：

- 搜索项目仓库名、项目镜像名、namespace、客户名和固定业务域名
- 除示例、注释和故障文档外，Workflow 不应出现当前项目的镜像仓库或 Release 名
- 项目默认值只能位于 `.image-build.env` 或用户明确指定的配置文件
- 未配置镜像地址时不得使用隐含的项目默认地址；应跳过模块并写出原因
- Release 名未配置时应从 `GITHUB_REPOSITORY` 的仓库名推导
- 复制到第二个项目时，只需修改配置文件和 Dockerfile，不应修改 CI 引擎脚本

通用性检查细则见 [references/genericity-audit.md](references/genericity-audit.md)。

## Workflow Summary 要求

配置 Job 至少展示：tag、Release 名、Dockerfile、Build context、两个基础镜像、两个主镜像名、每个模块状态和跳过原因。

每个架构 Build Job 展示：架构、平台、Runner、基础镜像、本地镜像、Aliyun 目标或跳过原因、Release 包名。

Release Job 展示：仓库、tag、架构、镜像引用、Artifact 文件名、SHA256、下载链接和 HAP 通知状态。Webhook payload 必须可直接作为 nginx-make 兼容 HAP Webhook 的请求体。

Summary 中不得输出密码、Token、Webhook 签名或完整 Secret 值。

## 排障顺序

遇到失败时先按以下顺序定位：

1. Workflow 是否解析成功，Job-level `if` 是否错误引用 `env`。
2. config Job 的 Outputs 是否为空，Summary 是否说明具体缺失项。
3. 失败 Job 是否 checkout 了仓库。
4. `DOCKER_CONTEXT`、`DOCKER_HOST`、`BUILDX_BUILDER` 等环境变量是否污染 Docker CLI。
5. setup-buildx 是否成功，构建脚本是否明确指定 Builder。
6. 基础镜像是否真的存在、可访问且平台正确。
7. Artifact 是否在上游成功上传，名称是否与下游下载名称一致。
8. Release manifest 是否按实际 Artifact 文件名正确识别 amd64/arm64。
9. HAP payload 是否包含固定字段、附件 URL 是否为 JSON 字符串、架构附件和 SHA256 是否来自实际 Release 产物。
10. HAP 通知是否只在 URL 和开关都满足时执行。

常见故障和对应检查见 [references/failure-patterns.md](references/failure-patterns.md)。完整交付检查见 [references/workflow-checklist.md](references/workflow-checklist.md)。

## 验证和交付

实现后至少执行：

- Python `ast.parse` 或等价语法检查
- `bash -n` 检查 CI Shell 脚本
- `git diff --check`
- 检查 Workflow 行为：push 触发、手动 build-only、手动 build-and-release、release-only、Aliyun 缺配置、HAP URL 缺失
- 对 Workflow 和 CI 脚本执行通用性审计，确认没有残留当前项目默认值
- 如本机没有 Docker，明确说明未执行真实镜像构建，不要声称构建已验证

用户要求提交时才执行 commit/push；提交前检查 `git status`，提交后报告 commit id 和目标分支。

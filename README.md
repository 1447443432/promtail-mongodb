# promtail-mongodb

GitHub Actions 使用 amd64/arm64 两个原生 Runner 分别构建镜像，暂不合并统一多架构 manifest。

默认本地构建镜像名：

```text
registry.cn-hangzhou.aliyuncs.com/hap-mdy/hap-promtail-vlogs-mongodb-amd64:1.0.0
registry.cn-hangzhou.aliyuncs.com/hap-mdy/hap-promtail-vlogs-mongodb-arm64:1.0.0
```

这里的主镜像名只用于 Docker build、Docker save 和 Release 打包，不需要登录主仓库。

阿里云推送为可选模块。阿里云目标镜像地址需要显式配置完整的镜像名和 Tag。配置完整时，流程为：

```text
docker build
docker tag 本地主镜像 阿里云镜像
docker push 阿里云镜像
```

例如：

```text
本地：a.com/a/hap-promtail-vlogs-mongodb-amd64:1.0.0
阿里云：registry.cn-hangzhou.aliyuncs.com/hap-mdy/hap-promtail-vlogs-mongodb-amd64:1.0.0
```

没有配置阿里云地址或账号密码时，只跳过阿里云 Push；构建仍然执行，Release 使用主镜像打包。配置阿里云后，Release 优先从阿里云镜像打包。

## Workflow 运行模式

使用 `Actions → Image Make → Run workflow` 时，`operation` 请选择以下模式之一：

- `build-release`：构建 amd64/arm64 镜像、生成压缩包和 SHA256，并创建 GitHub Release。
- `pull-release`：不重新构建，使用已有阿里云镜像打包并创建 GitHub Release。
- `build-push-release`：构建镜像、推送阿里云、打包并创建 GitHub Release。

这里的 `push` 仅表示 GitHub 的自动提交触发事件，不是手动运行模式。提交到 `master` 时，Workflow 默认执行 `build-push-release`；仅修改 `agents/` 时不会触发。

手动输入项的含义：

- `tag`：GitHub Release tag，必须显式提供；镜像 Tag 分别写在各镜像地址中
- `platforms`：参与构建的平台，默认 `linux/amd64,linux/arm64`
- `build_image`：构建模块开关；关闭后 `build-release` 和 `build-push-release` 不会构建
- `push_aliyun`：阿里云推送模块开关；关闭或配置不完整时只跳过推送
- `create_release`：Release 模块开关；关闭后不会打包上传 Release
- `notify_hap`：HAP Webhook 通知模块开关；关闭或 URL 为空时只跳过通知
- `target_image_amd64`、`target_image_arm64`：覆盖两个架构的完整主镜像地址，必须显式包含 tag
- `aliyun_namespace`：覆盖阿里云命名空间
- `aliyun_image_amd64`、`aliyun_image_arm64`：覆盖阿里云完整目标镜像地址，必须显式包含 tag

`pull-release` 需要提前存在可拉取的阿里云镜像和完整的阿里云凭据。如果只想构建而不创建 Release，可将 `create_release` 关闭；`build-release` 本身会创建 Release。

手动运行时必须填写 `tag`；自动提交时必须在 `.image-build.env` 或 Repository Variable 中显式配置 `IMAGE_TAG`，否则不会构建或发布。

## 架构基础镜像

amd64 和 arm64 的基础镜像地址可以完全不同，不能假设只替换镜像名中的架构字符串即可。请在 `.image-build.env` 中分别配置：

```bash
BASE_IMAGE_AMD64=registry.example.com/base/linux-amd64:3.23
BASE_IMAGE_ARM64=another.example.com/base/arm64-runtime:3.23
```

Workflow 会把对应值通过 `--build-arg BASE_IMAGE=...` 传给 Dockerfile。默认使用官方多架构 `alpine:3.23`，直接手动构建会按当前 Docker 平台自动选择 amd64 或 arm64：

```bash
docker build -t promtail-mongodb:amd64 .
```

需要指定不同基础镜像时，再显式传入：

```bash
docker build --build-arg BASE_IMAGE=another.example.com/base/arm64-runtime:3.23 -t promtail-mongodb:arm64 .
```

如果基础镜像仓库是私有仓库，可配置 Secrets `BASE_REGISTRY_USERNAME` 和 `BASE_REGISTRY_PASSWORD`。Workflow 会从当前架构的 `BASE_IMAGE_*` 地址自动解析 Registry 并在构建前登录，不需要额外配置 `BASE_REGISTRY_*`。

阿里云配置：

- Variable：`ALIYUN_REGISTRY`，默认 `registry.cn-hangzhou.aliyuncs.com`
- Secrets：`ALIYUN_REGISTRY_USERNAME`、`ALIYUN_REGISTRY_PASSWORD`
- Workflow 输入：`aliyun_namespace`，默认 `hap-mdy`
- `aliyun_image_amd64`、`aliyun_image_arm64`：阿里云目标镜像完整地址，必须显式包含 Tag

HAP 配置：

- Secret：`HAP_WEBHOOK_URL`
- 可选：`HAP_WEBHOOK_APP_KEY`、`HAP_WEBHOOK_SIGN`

HAP URL 为空时跳过通知，并在 Actions Summary 中说明原因。

HAP Webhook 的请求体与 nginx-make 保持一致，使用固定的通用字段，不携带项目专用字段。`project_name` 使用 `RELEASE_NAME`（未配置时使用仓库名），版本和附件信息从当前 Release 自动生成。`attachment_urls` 按 HAP 约定以 JSON 字符串传递多个下载地址。请求使用 `Content-Type: application/json`，并按配置附带 `AppKey`、`Sign` 请求头。

请求体示例：

```json
{
  "project_name": "promtail-mongodb",
  "repository": "1447443432/promtail-mongodb",
  "version": "1.0.0",
  "tag": "1.0.0",
  "release_url": "https://github.com/1447443432/promtail-mongodb/releases/tag/1.0.0",
  "amd64_name": "hap-promtail-vlogs-mongodb-amd64_1.0.0.tar.gz",
  "amd64_url": "https://github.com/1447443432/promtail-mongodb/releases/download/1.0.0/hap-promtail-vlogs-mongodb-amd64_1.0.0.tar.gz",
  "amd64_sha256": "...",
  "arm64_name": "hap-promtail-vlogs-mongodb-arm64_1.0.0.tar.gz",
  "arm64_url": "https://github.com/1447443432/promtail-mongodb/releases/download/1.0.0/hap-promtail-vlogs-mongodb-arm64_1.0.0.tar.gz",
  "arm64_sha256": "...",
  "attachment_urls": "[\"https://.../amd64.tar.gz\",\"https://.../arm64.tar.gz\"]",
  "commit_sha": "e7daeca",
  "run_id": "123456789",
  "run_url": "https://github.com/1447443432/promtail-mongodb/actions/runs/123456789",
  "build_status": "success"
}
```

amd64 和 arm64 附件字段始终存在；如果某架构没有产物，对应值为空字符串。Webhook 只在 Release 成功后发送，URL 为空或模块关闭时跳过并在 Summary 中说明原因。

## 手动 Docker 构建

Dockerfile 兼容直接手动构建，默认使用官方多架构 `alpine:3.23`：

```bash
docker build -t promtail-mongodb:amd64 .
```

在 arm64 主机上使用同一条命令即可；跨平台构建时指定平台：

```bash
docker buildx build --platform linux/arm64 --load -t promtail-mongodb:arm64 .
```

GitHub Actions 会根据矩阵自动传入 `TARGETARCH=amd64` 或 `TARGETARCH=arm64`。

## 项目配置文件

`.image-build.env` 是项目级默认配置。它使用简单的 `KEY=VALUE` 格式，支持 `#` 注释，适合直接复制到其他项目后修改。

`.github/workflows/image-make.yml` 和 `.github/image-make/` 不保存本项目的镜像仓库或 namespace；项目个性化值集中在 `.image-build.env`，因此这套 Workflow 可以直接复制到其他项目使用。

仅修改 `agents/` 下的 Skill 不会触发镜像构建；需要验证 Skill 时请手动运行 Workflow。

配置覆盖顺序从高到低为：

1. 手动 `Run workflow` 输入
2. GitHub Repository Variables
3. `.image-build.env`
4. Workflow 默认值

### 默认值与必填规则

需要注意：手动 `Run workflow` 页面显示的默认值，只对本次手动运行生效；`.image-build.env` 是项目级默认配置；Workflow 引擎本身不保存具体项目的镜像仓库默认值。

手动运行输入的默认值：

| 输入 | 默认值 | 是否必填 | 说明 |
|---|---|---|---|
| `operation` | `build-release` | 是 | `build-release` 构建并 Release；`pull-release` 拉取并 Release；`build-push-release` 构建、推送并 Release |
| `tag` | 空 | 是 | GitHub Release tag；必须显式提供 |
| `platforms` | `linux/amd64,linux/arm64` | 是 | 参与构建的平台 |
| `build_image` | `true` | 是 | 是否启用构建模块 |
| `push_aliyun` | `false` | 是 | 是否启用阿里云 Push；还必须满足阿里云配置完整 |
| `create_release` | `true` | 是 | 是否创建 GitHub Release |
| `notify_hap` | `false` | 是 | 是否启用 HAP 通知；还必须配置 Webhook URL |
| `target_image_amd64` | 空 | 否 | 空时使用 `.image-build.env` 或 Repository Variable；镜像地址必须自带 tag |
| `target_image_arm64` | 空 | 否 | 同上 |
| `aliyun_namespace` | 空 | 否 | 空时使用 `.image-build.env` 或 Repository Variable；没有完整阿里云配置只跳过 Push |
| `aliyun_image_amd64` | 空 | 否 | 阿里云 Push 或 pull-release 时必须显式提供带 tag 的完整地址 |
| `aliyun_image_arm64` | 空 | 否 | 同上 |

当前项目 `.image-build.env` 中的默认值如下：

```text
IMAGE_TAG=1.0.0
RELEASE_NAME=hap-promtail-vlogs-mongodb
BASE_IMAGE_AMD64=alpine:3.23
BASE_IMAGE_ARM64=alpine:3.23
TARGET_IMAGE_AMD64=registry.cn-hangzhou.aliyuncs.com/hap-mdy/hap-promtail-vlogs-mongodb-amd64:1.0.0
TARGET_IMAGE_ARM64=registry.cn-hangzhou.aliyuncs.com/hap-mdy/hap-promtail-vlogs-mongodb-arm64:1.0.0
ALIYUN_REGISTRY=registry.cn-hangzhou.aliyuncs.com
ALIYUN_NAMESPACE=hap-mdy
ENABLE_BUILD=true
ENABLE_ALIYUN_PUSH=true
ENABLE_RELEASE=true
ENABLE_HAP_WEBHOOK=true
```

没有默认值的配置：

- `HAP_WEBHOOK_URL`：没有默认值；为空时跳过 HAP 通知，并显示原因。
- `ALIYUN_REGISTRY_USERNAME`、`ALIYUN_REGISTRY_PASSWORD`：没有默认值；任一缺失时跳过阿里云 Push，但不阻断 Build 或 Release。
- `BASE_REGISTRY_USERNAME`、`BASE_REGISTRY_PASSWORD`：没有默认值；只有基础镜像仓库为私有仓库时才需要。
- `TARGET_IMAGE_AMD64`、`TARGET_IMAGE_ARM64`：通用 Workflow 没有默认镜像地址；当前项目的默认值来自 `.image-build.env`，且地址中的 tag 也必须显式填写。复制到其他项目时必须替换成新项目的完整镜像地址。

Dockerfile 的 `BASE_IMAGE` 默认值 `alpine:3.23` 只保证手动 `docker build .` 可用；CI 配置仍要求 `BASE_IMAGE_AMD64` 和 `BASE_IMAGE_ARM64` 都能解析到有效值，以避免架构基础镜像配置不明确。

## GitHub Actions 配置方法

所有 GitHub 端的配置入口都在仓库的：

```text
Settings → Secrets and variables → Actions
```

请分别进入 `Variables` 和 `Secrets` 标签页配置。配置完成后，打开：

```text
Actions → Image Make → Run workflow
```

手动执行一次验证。不要把密码、Webhook URL、AppKey 或 Sign 写入 README、`.image-build.env` 或 Workflow 文件。

### Repository Variables（可选覆盖项）

Variables 用于在 GitHub 侧覆盖非敏感配置，不是全部必填。在 `Settings → Secrets and variables → Actions → Variables → New repository variable` 中按需添加。当前项目已经有 `.image-build.env`，因此不需要把下面的值重复配置一遍；只有需要 GitHub 侧覆盖，或项目不提交 `.image-build.env` 时才配置 Variables。

| Name | 示例值/项目默认值 | 作用 |
|---|---|---|
| `IMAGE_TAG` | `1.0.0` | Push 事件使用的显式 Release tag；不配置则不构建/发布 |
| `RELEASE_NAME` | `promtail-mongodb` | Release 名和 HAP `project_name`；不配置时使用仓库名 |
| `TARGET_IMAGE_AMD64` | `registry.example.com/project/image-amd64:1.0.0` | amd64 主镜像完整地址，必须含 tag |
| `TARGET_IMAGE_ARM64` | `registry.example.com/project/image-arm64:1.0.0` | arm64 主镜像完整地址，必须含 tag |
| `BASE_IMAGE_AMD64` | `alpine:3.23` | amd64 基础镜像 |
| `BASE_IMAGE_ARM64` | `alpine:3.23` | arm64 基础镜像 |
| `ALIYUN_REGISTRY` | `registry.cn-hangzhou.aliyuncs.com` | 阿里云 Registry 地址 |
| `ALIYUN_NAMESPACE` | `hap-mdy` | 阿里云命名空间 |
| `ALIYUN_IMAGE_AMD64` | `registry.example.com/project/image-amd64:1.0.0` | 阿里云 amd64 完整镜像地址，必须含 tag |
| `ALIYUN_IMAGE_ARM64` | `registry.example.com/project/image-arm64:1.0.0` | 阿里云 arm64 完整镜像地址，必须含 tag |
| `ENABLE_BUILD` | `true` | 构建模块开关 |
| `ENABLE_ALIYUN_PUSH` | `true` | 阿里云 Push 模块开关 |
| `ENABLE_RELEASE` | `true` | GitHub Release 模块开关 |
| `ENABLE_HAP_WEBHOOK` | `true` | HAP Webhook 模块开关 |

本项目也可以把上述默认值写在 `.image-build.env`；两者同时存在时，Repository Variables 优先于 `.image-build.env`。`Run workflow` 页面中直接填写的输入优先级最高。

### Repository Secrets

Secrets 用于敏感配置。在 `Settings → Secrets and variables → Actions → Secrets → New repository secret` 中添加：

| Name | 是否必需 | 作用 |
|---|---|---|
| `ALIYUN_REGISTRY_USERNAME` | 使用阿里云 Push 时必需 | 阿里云 Registry 用户名 |
| `ALIYUN_REGISTRY_PASSWORD` | 使用阿里云 Push 时必需 | 阿里云 Registry 密码或 Access Token |
| `BASE_REGISTRY_USERNAME` | 基础镜像仓库私有时必需 | 基础镜像 Registry 用户名 |
| `BASE_REGISTRY_PASSWORD` | 基础镜像仓库私有时必需 | 基础镜像 Registry 密码或 Token |
| `HAP_WEBHOOK_URL` | 启用 HAP 通知时必需 | HAP Webhook 接收地址 |
| `HAP_WEBHOOK_APP_KEY` | 可选 | 作为 `AppKey` 请求头发送 |
| `HAP_WEBHOOK_SIGN` | 可选 | 作为 `Sign` 请求头发送 |

也兼容 `REGISTRY_USERNAME` 和 `REGISTRY_PASSWORD` 作为阿里云账号密码的通用别名，但建议统一使用 `ALIYUN_REGISTRY_USERNAME` 和 `ALIYUN_REGISTRY_PASSWORD`。

### HAP Webhook 配置示例

1. 在 HAP 中创建用于接收 Release 信息的 Webhook，并复制 Webhook URL。
2. 在 GitHub `Settings → Secrets and variables → Actions → Secrets` 中新增：

   ```text
   HAP_WEBHOOK_URL=https://your-hap.example.com/webhook/xxxxxxxx
   HAP_WEBHOOK_APP_KEY=your-app-key       # 如果 HAP 要求
   HAP_WEBHOOK_SIGN=your-sign             # 如果 HAP 要求
   ```

3. 在 Repository Variables 中设置：

   ```text
   ENABLE_HAP_WEBHOOK=true
   ```

4. 运行 `build-release` 或 `build-push-release`，Release 成功后才会执行 HAP 通知。

请求头和请求体如下：

```text
Content-Type: application/json
AppKey: <HAP_WEBHOOK_APP_KEY>   # 配置后才发送
Sign: <HAP_WEBHOOK_SIGN>        # 配置后才发送
```

Webhook URL 为空、`ENABLE_HAP_WEBHOOK` 不是 `true`，或 Release 没有成功时，不会调用 HAP；Actions Summary 会显示具体跳过原因。HAP 通知失败会使 Release Job 失败，便于及时发现接收端或签名配置错误。

### 阿里云 Push 配置示例

```text
Repository Variables:
  ALIYUN_REGISTRY=registry.cn-hangzhou.aliyuncs.com
  ALIYUN_NAMESPACE=hap-mdy
  ENABLE_ALIYUN_PUSH=true

Repository Secrets:
  ALIYUN_REGISTRY_USERNAME=<阿里云账号>
  ALIYUN_REGISTRY_PASSWORD=<阿里云密码或 Token>
```

阿里云配置及两个完整目标镜像地址都齐全时，Workflow 执行 `docker tag` 和 `docker push`。缺少 Registry、namespace、用户名、密码或目标镜像地址时，只跳过阿里云 Push，Build 和 Release 仍可继续；Release 会使用主镜像对应的本地构建产物。

### 配置后的验证建议

建议按以下顺序验证：

1. 先用 `build-release` 验证两个架构构建、打包和 Release。
2. 配置阿里云后用 `build-push-release` 验证 Tag、Push 和 Release 附件。
3. 配置 HAP 后再次运行 `build-release` 或 `build-push-release`，检查 Release Job 的 `HAP sync` 和通知步骤。
4. 检查 HAP 接收到的 `repository`、`version`、两个架构下载地址和 SHA256 是否正确。

如果某个可选模块没有配置，不要根据灰色步骤判断失败；查看 `Check module configuration` 和 `Release` 的 Actions Summary，其中会写明模块是关闭、缺少哪些配置，还是执行成功。

配置 Job 会在执行前检查所有模块，并把启用、跳过及缺失字段写入 Actions Summary。

## CI 专用脚本

项目运行脚本仍放在 `scripts/`。镜像构建 Workflow 使用的辅助脚本单独放在 `.github/image-make/`：

```text
.github/image-make/config.py   # 配置覆盖、模块开关和 Summary
.github/image-make/build.sh    # 单架构构建、Aliyun Push 和本地打包
.github/image-make/package.sh  # 构建产物校验或 Release-only 打包
.github/image-make/release.py  # Release manifest 和 Summary
```

`RELEASE_NAME` 写入 Release manifest。压缩包名称会根据镜像最后一段和 tag 自动生成，例如 `hap-promtail-vlogs-mongodb-amd64_1.0.0.tar.gz`。构建上下文配置项使用 `BUILD_CONTEXT`，不要命名为 Docker 保留的 `DOCKER_CONTEXT`。复制这套 Workflow 到其他项目时，只需要修改 `.image-build.env`、Dockerfile 和必要的镜像配置，不需要把 CI 脚本混入项目业务 `scripts/`。

Alpine 软件源由 `ALPINE_MIRROR` 和 `ALPINE_VERSION` 控制，默认使用阿里云源和 `3.23`。如果某个 Runner 访问阿里云源较慢，可以在 `.image-build.env` 中切换，例如：

```bash
ALPINE_MIRROR=https://dl-cdn.alpinelinux.org/alpine
ALPINE_VERSION=3.23
```

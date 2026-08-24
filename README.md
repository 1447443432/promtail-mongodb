# promtail-mongodb

GitHub Actions 使用 amd64/arm64 两个原生 Runner 分别构建镜像，暂不合并统一多架构 manifest。

默认本地构建镜像名：

```text
registry.cn-hangzhou.aliyuncs.com/hap-mdy/hap-promtail-vlogs-mongodb-amd64:1.0.0
registry.cn-hangzhou.aliyuncs.com/hap-mdy/hap-promtail-vlogs-mongodb-arm64:1.0.0
```

这里的主镜像名只用于 Docker build、Docker save 和 Release 打包，不需要登录主仓库。

阿里云推送为可选模块。阿里云目标镜像会自动根据本地镜像名生成。配置完整时，流程为：

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

- `build-only`：只构建 amd64/arm64 镜像，并上传构建产物；不创建 GitHub Release。
- `build-and-release`：构建镜像、按配置推送阿里云、打包并创建 GitHub Release。
- `release-only`：不重新构建，从已配置的阿里云镜像拉取对应架构镜像，打包并创建 GitHub Release。

这里的 `push` 仅表示 GitHub 的自动提交触发事件，不是手动运行模式。提交到 `master` 时，Workflow 默认执行 `build-and-release`；仅修改 `agents/` 时不会触发。

手动输入项的含义：

- `tag`：镜像 tag 和 GitHub Release tag
- `platforms`：参与构建的平台，默认 `linux/amd64,linux/arm64`
- `build_image`：构建模块开关；关闭后 `build-only` 和 `build-and-release` 不会构建
- `push_aliyun`：阿里云推送模块开关；关闭或配置不完整时只跳过推送
- `create_release`：Release 模块开关；关闭后不会打包上传 Release
- `notify_hap`：HAP Webhook 通知模块开关；关闭或 URL 为空时只跳过通知
- `target_image_amd64`、`target_image_arm64`：覆盖两个架构的主镜像名，不含 tag
- `aliyun_namespace`：覆盖阿里云命名空间
- `aliyun_image_amd64`、`aliyun_image_arm64`：覆盖阿里云目标镜像名，不含 tag

`release-only` 需要提前存在可拉取的阿里云镜像和完整的阿里云凭据；如果只想验证构建，请选择 `build-only`。

tag 默认是 `1.0.0`。手动运行时可修改 Workflow 输入；自动提交时可配置 Repository Variable `IMAGE_TAG`。

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
- `aliyun_image_amd64`、`aliyun_image_arm64` 可选，填写后覆盖自动推导结果

HAP 配置：

- Secret：`HAP_WEBHOOK_URL`
- 可选：`HAP_WEBHOOK_APP_KEY`、`HAP_WEBHOOK_SIGN`

HAP URL 为空时跳过通知，并在 Actions Summary 中说明原因。

HAP Webhook 的请求体与 nginx-make 保持一致，包含 `project_name`、`repository`、`version`、`tag`、`release_url`、amd64/arm64 的附件名称、下载地址和 SHA256，以及 `attachment_urls`、`commit_sha`、`run_id`、`run_url`、`build_status`。其中 `attachment_urls` 按 HAP 约定以 JSON 字符串传递多个下载地址。请求仍使用 `Content-Type: application/json`，并按配置附带 `AppKey`、`Sign` 请求头。

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

常用 Repository Variables：

```text
IMAGE_TAG
RELEASE_NAME
TARGET_IMAGE_AMD64
TARGET_IMAGE_ARM64
ALIYUN_REGISTRY
ALIYUN_NAMESPACE
ENABLE_BUILD
ENABLE_ALIYUN_PUSH
ENABLE_RELEASE
ENABLE_HAP_WEBHOOK
```

账号、密码和 Webhook 签名不要写入 `.image-build.env`，必须放在 GitHub Actions Secrets。配置 Job 会在执行前检查所有模块，并把启用、跳过及缺失字段写入 Actions Summary。

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

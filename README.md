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

使用 `Actions → Image Make → Run workflow`，可控制：

- `build_image`：是否构建镜像
- `push_aliyun`：是否推送阿里云
- `create_release`：是否创建 GitHub Release
- `notify_hap`：是否通知 HAP Webhook

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

配置覆盖顺序从高到低为：

1. 手动 `Run workflow` 输入
2. GitHub Repository Variables
3. `.image-build.env`
4. Workflow 默认值

常用 Repository Variables：

```text
IMAGE_TAG
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

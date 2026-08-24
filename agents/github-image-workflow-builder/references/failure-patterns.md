# 常见失败模式

## `context ".": context not found`

通常是把构建目录配置命名为 `DOCKER_CONTEXT=.`。Docker CLI 将该环境变量当作 Docker Context 名称。改用 `BUILD_CONTEXT=.`，并在 build 脚本中传给 `docker buildx build` 的最后一个参数。

## `no builder "" found`

构建脚本依赖空的 `BUILDX_BUILDER` 或 setup action 创建的临时 Builder，但脚本没有明确选择。使用固定的架构专属名称，例如 `image-make-amd64`，先 `docker buildx inspect`，不存在时 `docker buildx create --use`，构建时传 `--builder`。

## `No such file or directory: .github/...`

Job 是独立 Runner。不要假设 build Job 的工作区会传给 package/release；每个需要仓库脚本的 Job 都必须执行 checkout。

## `exec format error`

当前 Runner/Build 平台与基础镜像平台不一致。检查：

- arm64 是否使用 `ubuntu-24.04-arm`
- buildx 是否传 `--platform linux/arm64`
- `BASE_IMAGE_ARM64` 是否真实存在并支持 arm64
- 是否误用了 amd64 专用镜像作为 arm64 基础镜像

## Artifact 下载不到

检查上传和下载是否使用完全相同的名称，例如：

```text
release-amd64
release-arm64
```

同时确认上传步骤没有因 `release_enabled` 被跳过，且下游 Job 的条件依赖了正确的上游结果。

## Archive 架构识别错误

如果文件名是 `<image>-amd64_<tag>.tar.gz`，不能再用最后一个下划线后的内容作为架构，因为那是 tag。应去掉 `_<tag>.tar.gz` 后，与 amd64/arm64 主镜像的最后一段进行匹配。

## Aliyun 缺配置导致整个流程失败

Aliyun Push 必须独立判断。缺少 Registry、用户名或密码时：

1. config Summary 写出缺少字段
2. Build 继续
3. 使用本地镜像生成 Artifact
4. Release 继续，并引用主镜像
5. 不生成虚假的 `published_images`

## HAP Webhook 为空

Webhook URL 为空或开关关闭时，通知步骤应为 skipped 或不执行，并在 Release Summary 写出原因。不要使用空 URL 调用 `curl`，也不要让 Release 因通知模块未配置而失败。

## HAP 字段和 nginx-make 不一致

Webhook 请求体应使用统一的扁平字段：`project_name`、`repository`、`version`、`tag`、`release_url`、两种架构的 `*_name`/`*_url`/`*_sha256`、`attachment_urls`、`commit_sha`、`run_id`、`run_url`、`build_status`。`attachment_urls` 必须是 JSON 字符串，例如 `"[\"https://.../amd64.tar.gz\",\"https://.../arm64.tar.gz\"]"`，不能直接传数组。所有 URL 和 SHA256 都必须从实际 GitHub Release 产物生成，不能写示例地址。

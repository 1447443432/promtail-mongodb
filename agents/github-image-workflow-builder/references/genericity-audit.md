# Workflow 通用性审计

## 允许出现项目值的位置

项目个性化值可以出现在：

- `.image-build.env`
- 用户明确指定的 Repository Variables 或 Secrets
- Dockerfile 及其项目业务配置
- README 示例和当前项目的说明文档

项目个性化值不应出现在：

- `.github/workflows/image-make.yml` 的默认镜像地址
- `.github/image-make/config.py` 的项目默认值
- `.github/image-make/build.sh`、`package.sh`、`release.py` 的固定镜像名
- Job 输出、Artifact 命名逻辑中的固定项目字符串

## 必查字符串

在交付前执行类似检查：

```bash
rg -n "当前仓库名|当前镜像名|当前 namespace|客户名" \
  .github/workflows .github/image-make
```

命中的每一项都要判断是通用逻辑、示例注释还是残留个性化配置。残留配置应移入 `.image-build.env`。

## 默认值规则

推荐默认值：

- `IMAGE_TAG` 未配置时使用 `latest`；项目可在 `.image-build.env` 或 Repository Variable 中显式覆盖
- `PLATFORMS` 可以使用 `linux/amd64,linux/arm64`
- `BASE_IMAGE_AMD64`、`BASE_IMAGE_ARM64` 没有可靠通用值时留空并跳过 Build
- 主镜像地址没有通用值时留空并跳过 Build/Release；镜像地址若未带 Tag，由 Docker 使用 `latest`，不得由脚本拼接
- `ALIYUN_REGISTRY` 和 `ALIYUN_NAMESPACE` 没有通用值时留空并跳过 Aliyun Push
- `RELEASE_NAME` 未配置时使用 `GITHUB_REPOSITORY` 的最后一段
- `ALPINE_MIRROR`、`ALPINE_VERSION` 只有在 Dockerfile 确实是 Alpine 时才定义

不要为了让流程“默认能跑”而重新塞入某个项目的仓库地址或 namespace。

## 复制到第二个项目的验收

将 Workflow 和 `.github/image-make/` 复制到临时项目后，只修改：

```text
.image-build.env
Dockerfile
```

应能得到新的：

- 镜像名
- Release 名
- Artifact 文件名
- manifest 镜像引用
- Summary 配置内容

如果仍需修改 Workflow 或 CI 脚本，说明通用性没有达标。

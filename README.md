# promtail-mongodb

项目支持通过 GitHub Actions 构建并发布 `linux/amd64`、`linux/arm64` 多架构镜像。

同一个 Workflow 使用矩阵分别构建 amd64 和 arm64，生成带架构后缀的独立镜像；当前暂不合并统一的多架构 manifest。

使用 `Actions → Image Make → Run workflow`，各功能可独立开关：

推送到 `master` 分支时模块默认开启，但每个模块会先检查自己的地址、账号和密码；配置不完整时只跳过对应模块，并在 Actions Summary 中显示原因。自动触发使用 `sha-<commit>` 作为镜像和 Release tag。

- `build_image`：是否执行 Dockerfile 构建。
- `push_registry`：是否推送到主镜像仓库。
- `push_aliyun`：是否同时推送到阿里云镜像仓库。
- `create_release`：是否生成架构镜像包并创建 GitHub Release。
- `notify_hap`：Release 完成后是否通知 HAP Webhook。

操作模式：

- `build`：构建和推送镜像，不创建 Release。
- `release`：使用已有镜像生成 Release 包。
- `build-and-release`：构建、推送、打包并创建 Release。

主仓库默认镜像为：

```text
registry.cn-hangzhou.aliyuncs.com/hap-mdy/hap-promtail-vlogs-mongodb-amd64:1.0.0
registry.cn-hangzhou.aliyuncs.com/hap-mdy/hap-promtail-vlogs-mongodb-arm64:1.0.0
```

tag 默认是 `1.0.0`，手动运行时可在 Workflow 输入中修改；自动提交时可通过 Repository Variable `IMAGE_TAG` 修改。两个架构镜像地址也可以分别修改。开启 `push_aliyun` 后，需要分别填写阿里云 amd64/arm64 镜像地址。

需要在仓库 `Settings → Secrets and variables → Actions` 配置：

- 主仓库：Variable `REGISTRY`；Secrets `REGISTRY_USERNAME`、`REGISTRY_PASSWORD`
- 阿里云：可选 Variable `ALIYUN_REGISTRY`；Secrets `ALIYUN_REGISTRY_USERNAME`、`ALIYUN_REGISTRY_PASSWORD`
- HAP：Secret `HAP_WEBHOOK_URL`；如开启应用授权，再配置 `HAP_WEBHOOK_APP_KEY`、`HAP_WEBHOOK_SIGN`


阿里云账号未单独配置时，会回退使用主仓库账号。`notify_hap=true` 时，Webhook 收到的 `release-manifest.json` 包含已推送镜像、架构、Release 下载地址和 SHA256。

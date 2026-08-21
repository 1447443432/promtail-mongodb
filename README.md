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

阿里云配置：

- Variable：`ALIYUN_REGISTRY`，默认 `registry.cn-hangzhou.aliyuncs.com`
- Secrets：`ALIYUN_REGISTRY_USERNAME`、`ALIYUN_REGISTRY_PASSWORD`
- Workflow 输入：`aliyun_namespace`，默认 `hap-mdy`
- `aliyun_image_amd64`、`aliyun_image_arm64` 可选，填写后覆盖自动推导结果

HAP 配置：

- Secret：`HAP_WEBHOOK_URL`
- 可选：`HAP_WEBHOOK_APP_KEY`、`HAP_WEBHOOK_SIGN`

HAP URL 为空时跳过通知，并在 Actions Summary 中说明原因。

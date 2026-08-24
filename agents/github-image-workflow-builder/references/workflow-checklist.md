# GitHub Image Workflow 交付检查清单

## 项目扫描

- [ ] Dockerfile 可手动构建，且架构相关基础镜像没有被错误猜测
- [ ] 已读取现有 `.github/workflows/`、`scripts/`、README 和配置文件
- [ ] 没有覆盖用户未授权的工作区改动
- [ ] CI 辅助脚本与业务脚本分离
- [ ] 当前项目的镜像名、namespace 和 Release 名没有写入 CI 引擎

## 配置

- [ ] `IMAGE_TAG` 可由配置覆盖
- [ ] `RELEASE_NAME` 可由配置覆盖
- [ ] `BASE_IMAGE_AMD64` 与 `BASE_IMAGE_ARM64` 独立
- [ ] 主镜像名不要求认证
- [ ] Aliyun Registry、namespace、账号密码缺失时只跳过 Push
- [ ] HAP URL 缺失时只跳过通知
- [ ] 账号、密码、签名未写入仓库
- [ ] 没有使用 `DOCKER_CONTEXT` 作为构建目录变量
- [ ] Alpine 源和版本通过 `ALPINE_MIRROR`、`ALPINE_VERSION` 配置
- [ ] Dockerfile 没有重复执行 `apk update` 后再 `apk add --no-cache`

## 架构和 Job

- [ ] amd64：`linux/amd64` + `ubuntu-24.04`
- [ ] arm64：`linux/arm64` + `ubuntu-24.04-arm`
- [ ] 每个独立 Job 都 checkout
- [ ] buildx Builder 显式可用
- [ ] 正常构建 Job 的可视步骤已合并，登录和 Builder 初始化不重复展示
- [ ] 成功构建不刷屏输出完整 BuildKit 日志，失败时保留可定位错误日志
- [ ] Push、Pull、打包、manifest 和 Webhook 输出统一的阶段标题与成功/失败标记
- [ ] 构建参数传入正确架构的 `BASE_IMAGE`
- [ ] 没有意外创建统一多架构 manifest

## Artifact 和 Release

- [ ] 构建阶段使用 `docker save | gzip`
- [ ] 同时生成 SHA256
- [ ] 文件名形如 `<镜像最后一段>_<tag>.tar.gz`
- [ ] 下游下载的 Artifact 名称与上游一致
- [ ] Release manifest 能从文件名识别架构
- [ ] Aliyun 可用时 Release 使用 Aliyun 镜像引用
- [ ] Aliyun 不可用时 Release 使用主镜像引用
- [ ] `published_images` 只列实际 Push 成功的镜像

## Summary 和回归

- [ ] config Summary 展示最终配置和跳过原因
- [ ] amd64/arm64 Summary 展示平台、Runner、基础镜像和产物
- [ ] Release Summary 展示镜像、Archive、SHA256、下载链接
- [ ] Summary 不包含 Secret
- [ ] 检查 push
- [ ] 检查手动 build
- [ ] 检查手动 build-and-release
- [ ] 检查 release-only
- [ ] 检查 Aliyun 缺账号密码
- [ ] 检查 HAP URL 为空
- [ ] 用 `rg` 对 Workflow 和 CI 脚本执行项目个性化字符串审计
- [ ] 确认复制到第二个项目时只需修改 `.image-build.env` 和 Dockerfile

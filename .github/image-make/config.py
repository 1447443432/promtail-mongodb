#!/usr/bin/env python3
"""Resolve image workflow configuration and write GitHub outputs/summary."""

import os


def load_file(path):
    values = {}
    if not os.path.exists(path):
        return values
    with open(path, encoding="utf-8") as stream:
        for raw in stream:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip("\"'")
    return values


config = load_file(os.environ.get("CONFIG_FILE", ".image-build.env"))
event = os.environ.get("EVENT_NAME", "push")


def value(key, input_key=None, variable_key=None, default=""):
    if event != "push" and input_key and os.environ.get(input_key, "").strip():
        return os.environ[input_key].strip()
    if variable_key and os.environ.get(variable_key, "").strip():
        return os.environ[variable_key].strip()
    return config.get(key, default).strip()


tag = value("IMAGE_TAG", "INPUT_TAG", "VAR_IMAGE_TAG", "1.0.0")
repository_name = os.environ.get("GITHUB_REPOSITORY", "image").rsplit("/", 1)[-1]
release_name = value("RELEASE_NAME", None, "VAR_RELEASE_NAME", repository_name)
base_amd64 = value("BASE_IMAGE_AMD64", None, "VAR_BASE_IMAGE_AMD64")
base_arm64 = value("BASE_IMAGE_ARM64", None, "VAR_BASE_IMAGE_ARM64")
target_amd64 = value("TARGET_IMAGE_AMD64", "INPUT_TARGET_IMAGE_AMD64", "VAR_TARGET_IMAGE_AMD64")
target_arm64 = value("TARGET_IMAGE_ARM64", "INPUT_TARGET_IMAGE_ARM64", "VAR_TARGET_IMAGE_ARM64")
aliyun_namespace = value("ALIYUN_NAMESPACE", "INPUT_ALIYUN_NAMESPACE", "VAR_ALIYUN_NAMESPACE")
aliyun_registry = value("ALIYUN_REGISTRY", None, "VAR_ALIYUN_REGISTRY")
aliyun_amd64 = value("ALIYUN_IMAGE_AMD64", "INPUT_ALIYUN_IMAGE_AMD64", "VAR_ALIYUN_IMAGE_AMD64")
aliyun_arm64 = value("ALIYUN_IMAGE_ARM64", "INPUT_ALIYUN_IMAGE_ARM64", "VAR_ALIYUN_IMAGE_ARM64")
dockerfile = config.get("DOCKERFILE", "Dockerfile").strip()
build_context = config.get("BUILD_CONTEXT", ".").strip()
alpine_mirror = config.get("ALPINE_MIRROR", "https://mirrors.aliyun.com/alpine").strip()
alpine_version = config.get("ALPINE_VERSION", "3.23").strip()
platforms = (os.environ.get("WORKFLOW_PLATFORMS", "").strip() or config.get("PLATFORMS", "linux/amd64,linux/arm64").strip())
build_enabled = value("ENABLE_BUILD", "INPUT_BUILD_IMAGE", "VAR_ENABLE_BUILD", "true").lower() == "true"
aliyun_enabled = value("ENABLE_ALIYUN_PUSH", "INPUT_PUSH_ALIYUN", "VAR_ENABLE_ALIYUN_PUSH", "true").lower() == "true"
release_enabled = value("ENABLE_RELEASE", "INPUT_CREATE_RELEASE", "VAR_ENABLE_RELEASE", "true").lower() == "true"
hap_enabled = value("ENABLE_HAP_WEBHOOK", "INPUT_NOTIFY_HAP", "VAR_ENABLE_HAP_WEBHOOK", "true").lower() == "true"

primary = bool(target_amd64 and target_arm64)
aliyun_user = os.environ.get("ALIYUN_USERNAME", "").strip()
aliyun_password = os.environ.get("ALIYUN_PASSWORD", "").strip()
aliyun = aliyun_enabled and bool(aliyun_registry and aliyun_namespace and aliyun_user and aliyun_password and primary)
base = bool(base_amd64 and base_arm64)
can_build = build_enabled and primary and base
operation = os.environ.get("OPERATION", "build-release")
can_package = release_enabled and operation in ("build-release", "build-push-release", "pull-release") and (aliyun if operation == "pull-release" else can_build)
can_release = can_package

primary_missing = [name for name, item in (("TARGET_IMAGE_AMD64", target_amd64), ("TARGET_IMAGE_ARM64", target_arm64)) if not item]
aliyun_missing = [name for name, item in (("ALIYUN_REGISTRY", aliyun_registry), ("ALIYUN_NAMESPACE", aliyun_namespace), ("ALIYUN_USERNAME", aliyun_user), ("ALIYUN_PASSWORD", aliyun_password)) if not item]
reasons = []
if not aliyun_enabled:
    reasons.append("Aliyun push skipped; module is disabled.")
elif not aliyun:
    reasons.append("Aliyun push skipped; missing: " + ", ".join(aliyun_missing))
if not primary:
    reasons.append("Build skipped; missing primary image names: " + ", ".join(primary_missing))
if build_enabled and not base:
    reasons.append("Build skipped; BASE_IMAGE_AMD64 or BASE_IMAGE_ARM64 is missing.")
if release_enabled and can_release:
    reasons.append("GitHub Release: enabled.")
if not os.environ.get("HAP_WEBHOOK_URL", "").strip() or not hap_enabled:
    reasons.append("HAP Webhook skipped; disabled or HAP_WEBHOOK_URL is missing.")
else:
    reasons.append("HAP Webhook: configured and will be notified after Release.")


def status(ok, missing=""):
    return "ready" if ok else "skipped: " + missing


with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as summary:
    summary.write("# Image Make configuration\n\n")
    summary.write(f"- **Operation:** `{operation}`\n- **Release name:** `{release_name}`\n- **Release tag:** `{tag}`\n")
    summary.write(f"- **Dockerfile:** `{dockerfile}`\n- **Build context:** `{build_context}`\n\n")
    summary.write("| Module | Status | Details |\n|---|---|---|\n")
    summary.write(f"| Build | **{status(can_build)}** | enabled: `{str(build_enabled).lower()}`, bases: `{base_amd64 or 'missing'}` / `{base_arm64 or 'missing'}` |\n")
    summary.write(f"| Primary image names | **{status(primary, ', '.join(primary_missing))}** | `{target_amd64 or 'missing'}` / `{target_arm64 or 'missing'}` |\n")
    aliyun_status = "disabled" if not aliyun_enabled else status(aliyun, ", ".join(aliyun_missing))
    summary.write(f"| Aliyun push | **{aliyun_status}** | `{aliyun_registry}/{aliyun_namespace}` |\n")
    summary.write(f"| GitHub Release | **{status(can_release)}** | enabled: `{str(release_enabled).lower()}` |\n")
    summary.write(f"| HAP Webhook | **{'ready' if hap_enabled and os.environ.get('HAP_WEBHOOK_URL', '').strip() else 'skipped'}** | enabled: `{str(hap_enabled).lower()}` |\n\n")
    summary.write("## Decisions and skip reasons\n\n")
    summary.write("\n".join(f"- {item}" for item in reasons) + "\n")

outputs = {
    "tag": tag, "release_name": release_name, "platforms": platforms,
    "base_image_amd64": base_amd64, "base_image_arm64": base_arm64,
    "target_image_amd64": target_amd64, "target_image_arm64": target_arm64,
    "aliyun_image_amd64": aliyun_amd64, "aliyun_image_arm64": aliyun_arm64,
    "aliyun_registry": aliyun_registry, "aliyun_namespace": aliyun_namespace,
    "build_enabled": str(build_enabled).lower(), "aliyun_push_enabled": str(aliyun_enabled).lower(),
    "release_enabled": str(release_enabled).lower(), "hap_enabled": str(hap_enabled).lower(),
    "dockerfile": dockerfile, "build_context": build_context,
    "alpine_mirror": alpine_mirror, "alpine_version": alpine_version,
    "can_primary": str(primary).lower(), "can_aliyun": str(aliyun).lower(),
    "can_build": str(can_build).lower(), "can_package": str(can_package).lower(),
    "can_release": str(can_release).lower(),
}
with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
    for key, item in outputs.items():
        output.write(f"{key}={item}\n")

print("========== configuration result ==========")
print("[OK] configuration resolved")
print(f"tag={tag}")
print(f"build={'enabled' if build_enabled else 'disabled'}")
print(f"aliyun_push={'ready' if aliyun else 'skipped'}")
print(f"release={'ready' if can_release else 'skipped'}")

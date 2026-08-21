#!/usr/bin/env python3
"""Create the release manifest and write the Release job summary."""

import glob
import hashlib
import json
import os


def digest(path):
    result = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


tag = os.environ["RELEASE_TAG"]
release_name = os.environ["RELEASE_NAME"]
primary = {"amd64": os.environ["TARGET_IMAGE_AMD64"], "arm64": os.environ["TARGET_IMAGE_ARM64"]}
aliyun = {"amd64": os.environ["ALIYUN_IMAGE_AMD64"], "arm64": os.environ["ALIYUN_IMAGE_ARM64"]}
for architecture, image in aliyun.items():
    if not image or image == ":" + tag:
        local_name = primary[architecture].rsplit("/", 1)[-1].rsplit(":", 1)[0]
        aliyun[architecture] = f"{os.environ['ALIYUN_REGISTRY']}/{os.environ['ALIYUN_NAMESPACE']}/{local_name}:{tag}"

base = f"{os.environ['GITHUB_SERVER_URL']}/{os.environ['GITHUB_REPOSITORY']}/releases/download/{tag}"
images = []
for path in sorted(glob.glob("release-assets/*.tar.gz")):
    architecture = path.rsplit("_", 1)[1].removesuffix(".tar.gz")
    image = aliyun[architecture] if os.environ["PUSH_ALIYUN"] == "true" else primary[architecture]
    archive = os.path.basename(path)
    images.append({
        "architecture": architecture,
        "platform": f"linux/{architecture}",
        "image": image,
        "archive": archive,
        "sha256": digest(path),
        "download_url": f"{base}/{archive}",
    })

published = list(aliyun.values()) if os.environ["PUSH_ALIYUN"] == "true" else []
manifest = {
    "event": "image_release_ready",
    "release_name": release_name,
    "release_tag": tag,
    "image": images[0]["image"] if images else "",
    "published_images": published,
    "platforms": os.environ["PLATFORMS"].split(","),
    "images": images,
}
with open("release-assets/release-manifest.json", "w", encoding="utf-8") as output:
    json.dump(manifest, output, indent=2)

with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as summary:
    summary.write("# Create Release summary\n\n")
    summary.write(f"- **Repository:** `{os.environ['GITHUB_REPOSITORY']}`\n- **Tag:** `{tag}`\n\n")
    summary.write("| Architecture | Image | Archive | SHA256 |\n|---|---|---|---|\n")
    for item in images:
        summary.write(f"| `{item['architecture']}` | `{item['image']}` | [{item['archive']}]({item['download_url']}) | `{item['sha256']}` |\n")
    summary.write("\n## HAP sync\n\n")
    if os.environ.get("HAP_ENABLED") != "true":
        summary.write("HAP Webhook skipped: module is disabled.\n")
    elif not os.environ.get("HAP_WEBHOOK_URL", "").strip():
        summary.write("HAP Webhook skipped: HAP_WEBHOOK_URL is missing.\n")
    else:
        summary.write("HAP Webhook: configured; see the notification step for the request result.\n")

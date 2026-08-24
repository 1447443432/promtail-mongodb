#!/usr/bin/env bash
set -euo pipefail

if [[ "$PACKAGE_MODE" == release ]]; then
  printf '%s' "$ALIYUN_PASSWORD" | docker login "$ALIYUN_REGISTRY" --username "$ALIYUN_USERNAME" --password-stdin
  package_image="$ALIYUN_IMAGE"
  if [[ -z "$package_image" || "$package_image" == ":${TARGET_IMAGE##*:}" ]]; then
    image_name="${TARGET_IMAGE%:*}"
    image_name="${image_name##*/}"
    package_image="${ALIYUN_REGISTRY}/${ALIYUN_NAMESPACE}/${image_name}:${TARGET_IMAGE##*:}"
  fi
  docker pull --platform "linux/${ARCHITECTURE}" "$package_image"
  actual="$(docker image inspect "$package_image" --format '{{.Architecture}}')"
  test "$actual" = "$ARCHITECTURE"
  mkdir -p release-assets
  image_name="${TARGET_IMAGE%:*}"
  image_name="${image_name##*/}"
  archive="release-assets/${image_name}_${RELEASE_TAG}.tar.gz"
  docker save "$package_image" | gzip -9 > "$archive"
  sha256sum "$archive" > "$archive.sha256"
fi

{
  echo "## Package $ARCHITECTURE summary"
  echo
  echo "- **Mode:** \`$PACKAGE_MODE\`"
  if [[ "$PACKAGE_MODE" == release ]]; then
    echo "- **Source image:** \`$package_image\`"
  else
    echo "- **Source:** build job artifact \`release-$ARCHITECTURE\`"
  fi
  echo "- **Platform check:** \`linux/$ARCHITECTURE\`"
  image_name="${TARGET_IMAGE%:*}"
  image_name="${image_name##*/}"
  echo "- **Archive:** \`${image_name}_${RELEASE_TAG}.tar.gz\`"
} >> "$GITHUB_STEP_SUMMARY"

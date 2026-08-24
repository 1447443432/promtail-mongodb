#!/usr/bin/env bash
set -euo pipefail

builder="image-make-${ARCHITECTURE}"
if ! docker buildx inspect "$builder" >/dev/null 2>&1; then
  docker buildx create --name "$builder" --driver docker-container --use
else
  docker buildx use "$builder"
fi

docker buildx build --builder "$builder" \
  --platform "$PLATFORM" \
  --build-arg TARGETARCH="$ARCHITECTURE" \
  --build-arg BASE_IMAGE="$BASE_IMAGE" \
  --file "$DOCKERFILE" \
  --tag "$TARGET_IMAGE" \
  --load "$BUILD_CONTEXT"

aliyun_image="$ALIYUN_IMAGE_OVERRIDE"
if [[ -z "$aliyun_image" || "$aliyun_image" == ":${TARGET_IMAGE##*:}" ]]; then
  image_name="${TARGET_IMAGE%:*}"
  image_name="${image_name##*/}"
  aliyun_image="${ALIYUN_REGISTRY}/${ALIYUN_NAMESPACE}/${image_name}:${TARGET_IMAGE##*:}"
fi
if [[ "$PUSH_ALIYUN" == true ]]; then
  docker tag "$TARGET_IMAGE" "$aliyun_image"
  docker push "$aliyun_image"
fi

image_name="${TARGET_IMAGE%:*}"
image_name="${image_name##*/}"
if [[ "$RELEASE_ENABLED" == true ]]; then
  mkdir -p release-assets
  archive="release-assets/${image_name}_${RELEASE_TAG}.tar.gz"
  docker save "$TARGET_IMAGE" | gzip -9 > "$archive"
  sha256sum "$archive" > "$archive.sha256"
fi

{
  echo "## Build $ARCHITECTURE summary"
  echo
  echo "| Item | Value |"
  echo "|---|---|"
  echo "| Architecture | \`$ARCHITECTURE\` |"
  echo "| Platform | \`$PLATFORM\` |"
  echo "| Runner | \`$RUNNER\` |"
  echo "| Base image | \`$BASE_IMAGE\` |"
  echo "| Local image | \`$TARGET_IMAGE\` |"
  if [[ "$PUSH_ALIYUN" == true ]]; then
    echo "| Aliyun push | enabled: \`$aliyun_image\` |"
  else
    echo "| Aliyun push | skipped: registry credentials or destination are missing |"
  fi
  echo "| Release package | \`${image_name}_${RELEASE_TAG}.tar.gz\` |"
} >> "$GITHUB_STEP_SUMMARY"

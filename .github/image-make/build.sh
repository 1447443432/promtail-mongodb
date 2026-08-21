#!/usr/bin/env bash
set -euo pipefail

docker buildx build \
  --platform "$PLATFORM" \
  --build-arg TARGETARCH="$ARCHITECTURE" \
  --build-arg BASE_IMAGE="$BASE_IMAGE" \
  --file "$DOCKERFILE" \
  --tag "$TARGET_IMAGE" \
  --load "$DOCKER_CONTEXT"

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

if [[ "$RELEASE_ENABLED" == true ]]; then
  mkdir -p release-assets
  archive="release-assets/${RELEASE_NAME}_${RELEASE_TAG}_${ARCHITECTURE}.tar.gz"
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
  echo "| Release package | \`${RELEASE_NAME}_${RELEASE_TAG}_${ARCHITECTURE}.tar.gz\` |"
} >> "$GITHUB_STEP_SUMMARY"

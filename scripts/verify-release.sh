#!/usr/bin/env bash
set -euo pipefail

TAG="v0.1.0"
ASSET="WATCH-v0.1.0-windows.zip"
DESTINATION="${1:-artifacts/release-verification}"

mkdir -p "$DESTINATION"

export WATCH_RELEASE_JSON="$(
  gh release view "$TAG" --json tagName,name,isDraft,isPrerelease,assets,url
)"
python - "$ASSET" "$DESTINATION/release.json" <<'PY'
import json
import os
import pathlib
import sys

asset_name = sys.argv[1]
out_path = pathlib.Path(sys.argv[2])
payload = json.loads(os.environ["WATCH_RELEASE_JSON"])

if payload["tagName"] != "v0.1.0":
    raise SystemExit(f"Unexpected release tag: {payload['tagName']}")
if payload["isDraft"]:
    raise SystemExit("Release is still a draft")
if payload["isPrerelease"]:
    raise SystemExit("Release is marked as a prerelease")
assets = {asset["name"]: asset for asset in payload["assets"]}
if asset_name not in assets:
    raise SystemExit(f"Missing release asset: {asset_name}")
if int(assets[asset_name].get("size", 0)) <= 0:
    raise SystemExit(f"Release asset is empty: {asset_name}")

out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
PY
unset WATCH_RELEASE_JSON

gh release download "$TAG" --pattern "$ASSET" --dir "$DESTINATION" --clobber

test -s "$DESTINATION/$ASSET"
sha256sum "$DESTINATION/$ASSET" > "$DESTINATION/$ASSET.sha256"

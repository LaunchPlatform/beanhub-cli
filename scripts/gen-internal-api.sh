#!/usr/bin/env bash

uv run openapi-python-client generate \
  --path=data/internal-openapi.json \
  --config=data/internal-api-config.yaml \
  --output-path=internal_api_output

rm -rf beanhub_cli/internal_api
mv internal_api_output/internal_api/ beanhub_cli/
rm -rf internal_api_output/

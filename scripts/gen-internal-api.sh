#!/usr/bin/env bash

poetry run openapi-python-client generate \
  --path=data/internal-openapi.json \
  --config=data/internal-api-config.yaml \
  --output-path=internal_api_output

mv internal_api_output/internal_api/ beanhub_cli/internal_api
rm -rf internal_api_output/

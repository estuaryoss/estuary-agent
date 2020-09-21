#!/bin/bash

echo "$DOCKERHUB_TOKEN" | docker login -u "$DOCKERHUB_USERNAME" --password-stdin

#centos
\cp dist/start start.py
docker build -t dinutac/estuary-agent-centos:latest -f Dockerfile_centos .
docker push dinutac/estuary-agent-centos:latest

#for alpine clean everything
git reset --hard && git clean -dfx
git checkout "${TRAVIS_BRANCH}"

#alpine
docker build . -t dinutac/estuary-agent:latest
docker push dinutac/estuary-agent:latest
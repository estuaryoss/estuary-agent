#!/bin/bash

echo "$DOCKERHUB_TOKEN" | docker login -u "$DOCKERHUB_USERNAME" --password-stdin

#centos
\cp dist/start start.py
docker build -t estuaryoss/agent-centos:latest -f Dockerfiles/Dockerfile_centos .
docker push estuaryoss/agent-centos:latest

#for alpine clean everything
git reset --hard && git clean -dfx
git checkout "${TRAVIS_BRANCH}"

#alpine
docker build . -t estuaryoss/agent:latest
docker push estuaryoss/agent:latest
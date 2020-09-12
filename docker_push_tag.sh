#!/bin/bash

echo "$DOCKERHUB_TOKEN" | docker login -u "$DOCKERHUB_USERNAME" --password-stdin

#centos
\cp dist/start start.py
docker build -t estuaryoss/agent-centos:"${TRAVIS_TAG}" -f Dockerfiles/Dockerfile_centos .
docker push estuaryoss/agent-centos:"${TRAVIS_TAG}"

#for alpine clean everything
git reset --hard && git clean -dfx
git checkout tags/"${TRAVIS_TAG}" -b "${TRAVIS_TAG}"

#alpine
docker build . -t estuaryoss/agent:"${TRAVIS_TAG}"
docker push estuaryoss/agent:"${TRAVIS_TAG}"
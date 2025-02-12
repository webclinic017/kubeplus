#!/bin/bash

if (( $# < 1 )); then
    echo "./build-artifact.sh <latest | versioned>"
fi

artifacttype=$1

if [ "$artifacttype" = "latest" ]; then
    export GO111MODULE=on; export GOOS=linux; go build .
    docker build --no-cache -t gcr.io/cloudark-kubeplus/mutating-webhook-helper:latest .
fi

if [ "$artifacttype" = "versioned" ]; then
    version=`tail -1 versions.txt`
    echo "Building version $version"
    export GO111MODULE=on; export GOOS=linux; go build .
    #docker build -t lmecld/mutating-webhook-helper:$version .
    #docker push lmecld/mutating-webhook-helper:$version
    docker build --no-cache -t gcr.io/cloudark-kubeplus/mutating-webhook-helper:$version .
    docker push gcr.io/cloudark-kubeplus/mutating-webhook-helper:$version
fi




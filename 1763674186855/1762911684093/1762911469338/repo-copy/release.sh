#!/usr/bin/env bash
# Helper: commit, tag and push a release

git add -A
git commit -m "AGL v0.1: tests green, KB stable, UTF-8, safety suite"
git tag -a v0.1.0 -m "AGL v0.1 stable"

git push origin main

git push --tags

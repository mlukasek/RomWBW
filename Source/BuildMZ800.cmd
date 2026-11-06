@echo off
setlocal

pushd MZ800 && call Build || exit /b & popd

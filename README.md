# CUDA-Data-Race-Detector
A dynamic data race detector for CUDA programs

## Environment

[NVBit 1.3.1](https://github.com/NVlabs/NVBit) is the instrumentation framework used by this tool.

NOTE: Since NVBit changes its API several times, you should use the specific version rather than its newest release.

Put nvbit_release, test-apps at the root of the repo. (or modify app_dir and tool_dir in util.sh)

## Usage
put CUDA programs at test-apps inside a folder with the same name of the programs (together with source code and Makefile)

```bash
$ chmod +x ./utils.sh
$ ./utils.sh race_check_trace <appname>
```

or with pre-compiled binary

```bash
$ ./utils.sh make_tool race_check_trace
$ LD_PRELOAD=/<path to repo>/CUDA-Data-Race-Detector/tools/race_check_trace/race_check_trace.so <binary to run> | /<path to repo>/CUDA-Data-Race-Detector/scripts/race_check_helper.py
```

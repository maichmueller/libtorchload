#!/bin/bash

# do !/bin/bash -x to see all commands and variables expanded as they are called (-v for not expanded variables)

cuda=false
cuda_version=cpu
os=linux
build=debug # by default we would grab the debug package of libtorch (windows only)
version=1.9.0
target_dir=$(dirname $(readlink -f $0)) # target dir is the dir of this script by default
for i in "$@"; do
  case $i in
  -c=* | --cuda=*)
    cuda="${i#*=}"
    shift # past argument=value
    ;;
  -o=* | --os=*)
    os="${i#*=}"
    shift # past argument=value
    ;;
  -cv=* | --cuda-version=*)
    cuda_version="${i#*=}"
    shift # past argument=value
    ;;
  -b=* | --build-type=*)
    build="${i#*=}"
    shift # past argument=value
    ;;
  -t=* | --targetdir=*)
    target_dir="${i#*=}"
    shift # past argument=value
    ;;
  -v=* | --version=*)
    version="${i#*=}"
    shift # past argument=value
    ;;
  *)
    # unknown option
    ;;
  esac
done

if [ "$cuda" = true ]; then
  if [ "$cuda_version" = cpu ]; then
    echo "Cuda was set to $cuda, but cuda version is set to $cuda_version."
    exit 1
  fi
  cv="cu"
  major="\d{1,2}"
  minor="((?<=[_\-.])\d+)|((?<=\d{2})\d+)"
  v1=$(echo "$cuda_version" | grep -Po "$major" | head -1)
  v2=$(echo $cuda_version | grep -Po "$minor" | head -1)
  if [ -n "$v1" ]; then
    cv+=$v1
    if [ -n "$v2" ]; then
      cv+=$v2
    else
      cv+="0"
    fi
  fi
  cuda_version=$cv
fi

base_url=https://download.pytorch.org/libtorch/$cuda_version

os=$(echo "$os" | tr '[:upper:]' '[:lower:]')
if [ "$os" == "lin" ] || [ "$os" == "linux" ] || [ "$os" == "ubuntu" ]; then
    filename=libtorch-cxx11-abi-shared-with-deps-$version%2B$cuda_version.zip
elif [ "$os" == "win" ] || [ "$os" == "windows" ] || [ "$os" == "win10" ]; then
    filename=libtorch-win-shared-with-deps-$version%2B$cuda_version.zip
elif [ "$os" == "mac" ] || [ "$os" == "apple" ] || [ "$os" == "macos" ]; then
  if [ "$cuda" = true ]; then
    echo "CUDA setting '$cuda' and operating system '$os' are incompatible. Stopping."
    exit
  fi
  filename=libtorch-macos-$version.zip
else
  echo "Operating system $os not supported. Stopping."
fi

url=$base_url/$filename
bad_chars="\%2B"
replacement="+"
filename="${filename/$bad_chars/$replacement}" # decode the potential hexadecimal %2B as the '+' char

if [ ! -f "$target_dir/$filename" ]; then
  printf "%s\n" "File $filename not found."
  printf "%s\n" "Will attempt to download:" "OS: $os" "VERSION: $version" "CUDA: $cuda" "CUDA VERSION: $cuda_version" "BUILD: $build" "URL: $url" "TARGET DIR: $target_dir"
  wget --directory-prefix="$target_dir" "$url" --no-verbose
else
  echo "Folder 'libtorch' already exists."
fi

unzip -q "$target_dir/$filename" -d "$target_dir"
rm "$target_dir/$filename"
if [ "$(echo "$build" | tr '[:upper:]' '[:lower:]')" == "debug" ]; then
  mv "$target_dir/libtorch" "$target_dir/libtorch_debug"
fi

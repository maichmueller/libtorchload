#!/bin/bash

# do !/bin/bash -x to see all commands and variables expanded as they are called (-v for not expanded variables)

cuda=false
cuda_version=cpu
os=linux
build=debug  # by default we would grab the debug package of libtorch (windows only)
target_dir=$(dirname $(readlink -f $0))  # target dir is the dir of this script by default
for i in "$@"
do
case $i in
    -c=*|--cuda=*)
    cuda="${i#*=}"
    shift # past argument=value
    ;;
    -s=*|--os=*)
    os="${i#*=}"
    shift # past argument=value
    ;;
    --cuda_version=*)
    cuda_version="${i#*=}"
    shift # past argument=value
    ;;
    -b=*|--build=*)
    build="${i#*=}"
    shift # past argument=value
    ;;
    -t=*|--targetdir=*)
    target_dir="${i#*=}"
    shift # past argument=value
    ;;
    *)
          # unknown option
    ;;
esac
done

if [ "$cuda_version" == "10" ] || \
   [ "$cuda_version" == "102" ] || \
   [ "$cuda_version" == "10-2" ] || \
   [ "$cuda_version" == "10.2" ]; then \
  cuda_version=cu102; \
elif [ "$cuda_version" == "101" ] || \
     [ "$cuda_version" == "10-1" ] || \
     [ "$cuda_version" == "10.1" ]; then \
  cuda_version=cu101; \
elif [ "$cuda_version" == "11" ] || \
     [ "$cuda_version" == "110" ] || \
     [ "$cuda_version" == "11-0" ] || [ "$cuda_version" == "11.0" ]; then \
  cuda_version=cu110; \

  filename=libtorch-macos-$version.zip; \

else
  echo "Operating system $os not supported. Stopping."
fi
base_url=https://download.pytorch.org/libtorch/$cuda_version
if [ "$cuda" = true ]; then \
  if [ "$cuda_version" = cpu ]; then \
    echo "Cuda was set to $cuda, but cuda version is set to $cuda_version."
    exit 1
  fi
fi

version=1.7.0
os=$(echo "$os" | tr '[:upper:]' '[:lower:]')
if [ "$os" == "lin" ] || [ "$os" == "linux" ] || [ "$os" == "ubuntu" ]; then \
  if [ "$cuda" = true ]; then \
    filename=libtorch-cxx11-abi-shared-with-deps-$version.zip; \
  else
    filename=libtorch-cxx11-abi-shared-with-deps-$version%2Bcpu.zip; \
  fi

elif [ "$os" == "mac" ] || [ "$os" == "apple" ] || [ "$os" == "macos" ]; then \
  if [ "$cuda" = true ]; then \
    echo "CUDA setting '$cuda' and operating system '$os' are incompatible. Stopping.";
  fi

  filename=libtorch-macos-$version.zip; \

else
  echo "Operating system $os not supported. Stopping."
fi
url=$base_url/$filename
bad_chars="\%2B"
replacement="+"
filename="${filename/$bad_chars/$replacement}"   # decode the potential hexadecimal %2B as the '+' char


printf "%s\n" "Will attempt to download:" "OS: $os" "CUDA: $cuda" "CUDA VERSION: $cuda_version" "BUILD: $build" "URL: $url" "TARGET DIR: $target_dir"

if [ ! -d "$target_dir"/libtorch ]; then \
  wget --directory-prefix="$target_dir" $url --no-verbose; \
  unzip "$target_dir"/$filename -d "$target_dir"; \
  rm "$target_dir"/$filename; \
else
  echo "Folder 'libtorch' already exists. Stopping."; \
fi
import warnings

import requests
import argparse
import sys
import zipfile
import os
import urllib.request
import re
from tqdm import tqdm


class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)


def download_url(url, name, ext, folder: str = ".", overwrite=False):
    fname = f"{name}.{ext}"
    fpath = os.path.join(folder, fname)
    if os.path.isfile(fpath) and not overwrite:
        print(
            f"File '{fname}' already exists in folder '{os.path.join(folder)}'. Stopping"
        )
        return fpath
    with DownloadProgressBar(
        unit="B", unit_scale=True, miniters=1, desc=url.split("/")[-1]
    ) as t:
        urllib.request.urlretrieve(url, filename=fpath, reporthook=t.update_to)
    return fpath


def parse_cuda_version(v):
    cv = "cu"
    major = re.search(r"\d\d?", v)
    minor = re.search(r"((?<=[_\-.])\d+)|((?<=\d{2})\d+)", v)
    if v == "cpu":
        cv = "cpu"
    elif major is not None:
        cv += major.group()
        if minor is not None:
            cv += minor.group()
        else:
            cv += "0"
    else:
        warnings.warn(
            "Version arg could not be identified. Continuing with torch CPU version."
        )
        cv = "cpu"
    return cv


def scrape_version():
    from bs4 import BeautifulSoup

    page = requests.get("https://pytorch.org/get-started/locally/")
    soup = BeautifulSoup(page.content, "html.parser")
    version_div = soup.find("div", class_="col-md-4 option block version selected")
    version_str = str(version_div.find("div", class_="option-text").contents[0])
    version = re.search(r"(?<=\()[\w.]+(?=\))", version_str).group()
    return version


def parse_os(platform, cuda: bool, build: str):
    if platform in ["lin", "linux", "ubuntu", "unix"]:
        fname = "libtorch-cxx11-abi-shared-with-deps"

    elif platform in ["mac", "apple", "macos", "osx"]:
        if cuda:
            raise ValueError(
                f"CUDA setting {cuda} and operating system {platform} are incompatible. Stopping."
            )
        fname = "libtorch-macos"

    elif platform in ["win", "windows", "win10", "win64", "win32"]:
        if build.lower() == "debug":
            fname = "libtorch-win-shared-with-deps-debug"
        else:
            fname = "libtorch-win-shared-with-deps"

    return fname


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cuda",
        type=bool,
        nargs="?",
        help="Whether to download the CUDA enabled library.",
    )

    parser.add_argument(
        "--os", type=str, nargs="?", default=sys.platform, help="The operating system",
    )

    parser.add_argument(
        "--cuda_version",
        metavar="the cuda version to load (or cpu)",
        type=str,
        nargs="?",
        default="cpu",
        help="Step from which to start",
    )

    parser.add_argument(
        "--build",
        metavar="library build type (debug or release)",
        type=str,
        nargs="?",
        default="debug",
        help="The build type.",
    )

    parser.add_argument(
        "--targetdir",
        metavar="download directory",
        type=str,
        nargs="?",
        default=".",
        help="The target directory in which to place the libtorch library",
    )

    parser.add_argument(
        "--version",
        metavar="version of libtorch",
        type=str,
        nargs="?",
        default="",
        help="The version of libtorch to download. Scrapes from website if not provided.",
    )
    parser.add_argument(
        "--force",
        metavar="force",
        type=bool,
        nargs="?",
        default=False,
        help="Whether to force a redownload, if the file already exists.",
    )

    args = parser.parse_args()
    cuda = args.cuda
    cuda_version = parse_cuda_version(args.cuda_version)
    if cuda_version:
        cuda = not cuda_version == "cpu"
    build = args.build
    targetdir = args.targetdir
    version = args.version
    platform = args.os
    force = args.force
    filename = parse_os(platform, cuda, build)

    if version == "":
        try:
            from bs4 import BeautifulSoup

            version = scrape_version()

        except ModuleNotFoundError as e:
            e.msg += (
                "\nIf no cuda version information is provided, it is scraped from 'pytorch.org'."
                " Package 'beautifulsoup4' is needed for this."
            )
            raise e
    filename += f"-{version}"
    if cuda_version == "cpu":
        filename += r"%2Bcpu"
    ext = "zip"

    if cuda:
        if cuda_version == "cpu":
            raise ValueError(
                f"cuda was chosen, but cuda toolkit version {cuda_version} was selected."
            )

    url = f"https://download.pytorch.org/libtorch/{cuda_version}/{filename}.{ext}"

    fpath = download_url(
        url, filename.replace("%2B", "+"), ext, folder=targetdir, overwrite=force
    )
    if (
        any(
            os.path.isdir(os.path.join(targetdir, folder))
            for folder in ("libtorch", "libtorch_debug")
        )
        and not force
    ):
        pass
    else:
        print("Unpacking...", end="")
        with zipfile.ZipFile(fpath, "r") as zip_ref:
            for elem in zip_ref.namelist():
                zip_ref.extract(elem, targetdir)
        print("done.")
    if "win" in platform and build == "debug":
        os.rename("libtorch", "libtorch_debug")
    os.remove(fpath)


if __name__ == "__main__":
    main()

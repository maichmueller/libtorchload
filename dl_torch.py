import requests
import argparse
import sys
import zipfile
import os
import urllib.request
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
        print(f"File '{fname}' already exists in folder '{os.path.join(folder)}'. Stopping")
        return fpath
    with DownloadProgressBar(
            unit="B", unit_scale=True, miniters=1, desc=url.split("/")[-1]
    ) as t:
        urllib.request.urlretrieve(url, filename=fpath, reporthook=t.update_to)
    return fpath


def parse_cuda_version(v):
    if v in ["10", "102", "10-2", "10.2"]:
        cv = "cu102"
    elif v in ["101", "10-1", "10.1"]:
        cv = "cu101"
    elif v in ["11", "110", "11-0", "11.0"]:
        cv = "cu110"
    else:
        cv = "cpu"
    return cv


def scrape_version():
    import re
    page = requests.get("https://pytorch.org/get-started/locally/")
    soup = BeautifulSoup(page.content, 'html.parser')
    version_div = soup.find("div", class_="col-md-6 option block version selected")
    version_str = str(version_div.find("div", class_="option-text").contents[0])
    version = re.search(r"(?<=\()[\w.]+(?=\))", version_str).group()
    return version


def parse_os(platform, cuda: bool, build: str):
    if platform in ["lin", "linux", "ubuntu"]:
        fname = f"libtorch-cxx11-abi-shared-with-deps"

    elif platform in ["mac", "apple", "macos"]:
        if cuda:
            raise ValueError(f"CUDA setting {cuda} and operating system {platform} are incompatible. Stopping.")
        fname = "libtorch-macos"

    elif platform in ["win", "windows", "win10", "win64", "win32"]:
        if build.lower() == "debug":
            fname = "libtorch-win-shared-with-deps-debug"
        else:
            fname = "libtorch-win-shared-with-deps"

    return fname


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cuda", type=bool, nargs="?", help="Whether to download the CUDA enabled library.",
    )

    parser.add_argument(
        "--os",
        type=str,
        nargs="?",
        default=sys.platform,
        help="The operating system",
    )

    parser.add_argument(
        "--cuda_version", type=str, nargs="?", default="cpu", help="Step from which to start",
    )

    parser.add_argument(
        "--build",
        type=str,
        nargs="?",
        default="debug",
        help="The build type.",
    )

    parser.add_argument(
        "--targetdir",
        type=str,
        nargs="?",
        default=".",
        help="The target directory in which to place the libtorch library",
    )

    parser.add_argument(
        "--version",
        metavar="version",
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
            e.msg += "\nIf no cuda version information is provided, it is scraped from 'pytorch.org'." \
                         " Package 'beautifulsoup4' is needed for this."
            raise e
    filename += f"-{version}"
    if cuda_version == "cpu":
        filename += r"%2Bcpu"
    ext = "zip"

    if cuda:
        if cuda_version == "cpu":
            raise ValueError(f"cuda was chosen, but cuda toolkit version {cuda_version} was selected.")

    url = f"https://download.pytorch.org/libtorch/{cuda_version}/{filename}.{ext}"

    fpath = download_url(url, filename.replace("%2B", "+"), ext, folder=targetdir, overwrite=force)
    if any(os.path.isdir(os.path.join(targetdir, folder)) for folder in ("libtorch", "libtorch_debug")) and not force:
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

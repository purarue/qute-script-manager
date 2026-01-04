from __future__ import annotations
import os

import typing
import hashlib
import tomllib
import filecmp
import time
import shlex
import subprocess
import shutil
from datetime import datetime
from urllib.parse import urlsplit
from pathlib import Path

import requests
import click
import tomli_w
import prettytable


@click.group()
def main() -> None:
    pass


def pager(file1: Path, file2: Path) -> None:
    # if user has a core.pager set, use that
    if shutil.which("git"):
        proc = subprocess.run(
            shlex.split("git config --global core.pager"),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    dproc = subprocess.Popen(
        [proc.stdout.decode().strip() or "diff", str(file1), str(file2)]
    )
    dproc.wait()


prog_name = "qute_script_manager"
config_base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
config_dir = config_base / prog_name
config_dir.mkdir(parents=True, exist_ok=True)

config_file = config_dir / "urls.toml"
cache_base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
cache_dir: Path = cache_base / prog_name

local_share = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
userscripts_dir = local_share / "qutebrowser" / "greasemonkey"


def epoch() -> int:
    return int(time.time())


def url_filename(base: Path, url: str) -> Path:
    """
    use the basename part of the URL as part of the directory structure
    limit path parts to 64 characters, some are really long
    """
    last_part = urlsplit(url).path.strip("/").split("/")[-1]
    if len(last_part) > 64:
        name, ext = os.path.splitext(last_part)
        base /= f"{name[:61]}{ext}"
    else:
        base /= last_part
    return base


class ScriptData(typing.NamedTuple):
    url: str
    nickname: str
    pinned: bool
    last_updated: int
    needs_update: bool

    @classmethod
    def from_raw(cls, d: typing.Any) -> typing.Self:
        if not isinstance(d, dict):
            raise TypeError(f"Expected dict, got {type(d)}")
        return cls(
            pinned=d.get("pinned", False),
            last_updated=d["last_updated"],
            url=d["url"],
            needs_update=d["needs_update"],
            nickname=d["nickname"],
        )

    @property
    def hash(self) -> str:
        return hashlib.md5(self.url.encode()).hexdigest()

    @property
    def cellar_dir(self) -> Path:
        c = cache_dir / self.hash
        c.mkdir(parents=True, exist_ok=True)
        return c

    @property
    def cellar_path(self) -> Path:
        cd = self.cellar_dir
        target_file = url_filename(cd, self.url)
        return target_file

    @property
    def filename(self) -> str:
        return self.cellar_path.name

    @property
    def local_share_path(self) -> Path:
        if not userscripts_dir.exists():
            raise FileNotFoundError(
                f"Could not find target qutebrowser directory {userscripts_dir}"
            )
        return userscripts_dir / self.filename

    def update_cellar_script(self, noconfirm: bool, skipcopy: bool) -> ScriptData:
        # dont update
        if self.pinned:
            return self
        target_file = self.cellar_path
        target_file.parent.mkdir(exist_ok=True, parents=True)
        resp = requests.get(self.url, stream=True)
        time.sleep(1)
        if resp.status_code != 200:
            click.echo(f"Downloading '{self.url}' failed", err=True)
            return self

        # stream to file
        click.echo(f"Fetching cellar file '{target_file}'", err=True)
        with open(target_file, "wb") as f:
            for chunk in resp:
                f.write(chunk)

        if skipcopy:
            return ScriptData(
                url=self.url,
                nickname=self.nickname,
                pinned=self.pinned,
                last_updated=self.last_updated,
                needs_update=self.local_share_path.exists() is False
                or not filecmp.cmp(self.cellar_path, self.local_share_path),
            )

        updated_time = self.last_updated
        local_path_exists = self.local_share_path.exists()
        if noconfirm is True:
            self.copy_cellar_to_local()
            updated_time = epoch()
        else:
            # show diff and ask if the user wants to copy
            if not local_path_exists and click.confirm(
                f"Install {self.nickname} {self.url} ?"
            ):
                self.copy_cellar_to_local()
                updated_time = epoch()
            else:
                pager(self.cellar_path, self.local_share_path)
                differs = not filecmp.cmp(self.cellar_path, self.local_share_path)
                if differs and click.confirm(f"Update {self.nickname} ?"):
                    self.copy_cellar_to_local()
                    updated_time = epoch()
                else:
                    click.echo(f"{self.nickname} is already up to date")

        return ScriptData(
            url=self.url,
            nickname=self.nickname,
            pinned=self.pinned,
            last_updated=updated_time,
            needs_update=self.needs_update,
        )

    def copy_cellar_to_local(self) -> None:
        click.echo(f"Copying {self.cellar_path} to {self.local_share_path}")
        shutil.copyfile(self.cellar_path, self.local_share_path)


type Config = dict[str, ScriptData]


def read_config(path: Path | None = None) -> Config:
    path = path or config_file
    if not path.exists():
        return {}
    else:
        with path.open("rb") as f:
            cfg = tomllib.load(f)
            assert isinstance(cfg, dict)
        cfg_dict: dict[str, ScriptData] = {}
        for k, v in cfg.items():
            cfg_dict[k] = ScriptData.from_raw(v)
        return cfg_dict


def write_config(*, conf: Config, fileobj: typing.BinaryIO) -> None:
    write_data: dict[str, typing.Any] = {}
    write_data = {}
    for k, v in conf.items():
        write_data[k] = v._asdict()
    tomli_w.dump(write_data, fileobj)


@main.command(short_help="add a URL")
@click.option("--nickname", help="set a nickname for this script", prompt=True)
@click.argument("URL", required=True)
def add(url: str, nickname: str) -> None:
    cfg = read_config()
    cfg[url] = ScriptData(
        url=url,
        nickname=nickname,
        pinned=False,
        last_updated=epoch(),
        needs_update=False,
    )
    with open(config_file, "wb") as f:
        write_config(conf=cfg, fileobj=f)


@main.command(short_help="print tracked scripts")
@click.option("-u", "--urls", is_flag=True, default=False, help="include URLs")
def list(urls: bool) -> None:
    cfg = read_config()
    headers = ["name", "pinned", "last updated", "needs update"]
    if urls:
        headers.insert(1, "url")
    pt = prettytable.PrettyTable(field_names=headers)
    for v in cfg.values():
        r = [
            v.nickname,
            v.pinned,
            datetime.fromtimestamp(int(v.last_updated)),
            v.needs_update,
        ]
        if urls:
            r.insert(1, v.url)
        pt.add_row(r)
    click.echo(str(pt))


@main.command()
@click.option(
    "--noconfirm",
    is_flag=True,
    default=False,
    help="skip asking for confirmation",
)
@click.option(
    "--skipcopy",
    is_flag=True,
    default=False,
    help="dont copy file to qutebrowser directory, just check for updates",
)
def update(skipcopy: bool, noconfirm: bool) -> None:
    cfg = read_config()
    updated: dict[str, ScriptData] = {}
    for sc in cfg.values():
        updated[sc.url] = sc.update_cellar_script(
            noconfirm=noconfirm, skipcopy=skipcopy
        )
    with open(config_file, "wb") as f:
        write_config(conf=updated, fileobj=f)


if __name__ == "__main__":
    main(prog_name="qute_script_manager")

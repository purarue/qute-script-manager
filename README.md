# qute_script_manager

This is a basic script to manage updating local copies of userscripts.

You can use `qute_script_manager add` to add a URL, `list` to list the currently tracked ones, and `update` to print a diff/install new versions of each userscript.

Does not support removing an installed userscript, you should do that by removing the file in `~/.local/share/qutebrowser/greasemonkey/`.

You can edit the `~/.config/qute_script_manager/urls.toml` to `pin` a version (skip updating) or remove a script from the tracked URLs.

## Installation

Requires `python3.12+`

To install with pip, run:

```
pip install git+https://github.com/purarue/qute_script_manager
```

## Usage

```
Usage: qute_script_manager [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  add     add a URL
  list    print tracked scripts
  update  update scripts
```

Update options:

```
Usage: qute_script_manager update [OPTIONS]

Options:
  --noconfirm  skip asking for confirmation
  --skipcopy   dont copy file to qutebrowser directory, just check for updates
  --help       Show this message and exit.
```

### Tests

```bash
git clone 'https://github.com/purarue/qute_script_manager'
cd ./qute_script_manager
pip install '.[testing]'
pytest
flake8 ./qute_script_manager
mypy ./qute_script_manager
```

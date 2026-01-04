# qute_script_manager

qutebrowser userscript manager

## Installation

Requires `python3.10+`

To install with pip, run:

```
pip install git+https://github.com/purarue/qute_script_manager
```

## Usage

```
qute_script_manager --help
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

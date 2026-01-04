# qusrm

qutebrowser userscript manager

## Installation

Requires `python3.10+`

To install with pip, run:

```
pip install git+https://github.com/purarue/qusrm
```

## Usage

```
qusrm --help
```

### Tests

```bash
git clone 'https://github.com/purarue/qusrm'
cd ./qusrm
pip install '.[testing]'
pytest
flake8 ./qusrm
mypy ./qusrm
```

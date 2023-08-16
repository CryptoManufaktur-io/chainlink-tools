
## EA Update tool

Python script that pulls new EA versions and updates them in a compose-style yaml

### Install requirements
```bash
pip install -r requirements.txt
```

### Run the tool

To update for example ea.yaml automatically, run the script `eaupdate.py` with arguments as follows:

```bash
./eaupdate.py Latest ea.yaml Confirm
```

The script expects 3 arguments
1. Release version of https://github.com/smartcontractkit/external-adapters-js/releases . When Latest is provided, it will get the latest stable version automatically
2. Yaml file to update
3. Overwrite yaml wile automatically (True), Don't overwrite at all (False), Ask before action (Confirm) which is the default when not provided.

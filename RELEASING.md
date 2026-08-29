# Releasing

Releases use PyPI trusted publishing through GitHub Actions. No PyPI API token
or GitHub repository secret is needed.

## One-time publisher setup

PyPI and TestPyPI use separate accounts and publisher registrations. Sign in
to each service, verify the account email address, and add a pending GitHub
publisher with these values:

| Field | PyPI | TestPyPI |
| --- | --- | --- |
| PyPI project name | `ina229-ft232h` | `ina229-ft232h` |
| GitHub owner | `SiboVG` | `SiboVG` |
| GitHub repository | `ina229-ft232h` | `ina229-ft232h` |
| Workflow filename | `publish.yml` | `publish.yml` |
| Environment | `pypi` | `testpypi` |

- PyPI publisher setup: <https://pypi.org/manage/account/publishing/>
- TestPyPI publisher setup: <https://test.pypi.org/manage/account/publishing/>

Do not create or store `PYPI_TOKEN` or `TEST_PYPI_TOKEN` secrets. GitHub obtains
a short-lived token from each index for an authorized workflow run.

## TestPyPI

Run the `Publish` workflow manually from the GitHub Actions page. A manual run
builds and validates the distributions, then uploads them only to TestPyPI.
Test the uploaded wheel in a clean environment with dependencies sourced from
regular PyPI:

```bash
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  ina229-ft232h==0.1.0
```

## PyPI

After the TestPyPI installation succeeds:

1. Create and push a `v0.1.0` tag for version `0.1.0`.
2. Publish a GitHub Release for that tag.
3. Approve the `pypi` environment deployment when GitHub asks.

Publishing the GitHub Release runs the same build and validation process and
uploads the distributions to PyPI. The workflow rejects a release tag that
does not match the version in `pyproject.toml`.

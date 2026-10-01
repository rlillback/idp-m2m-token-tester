# idp-m2m-token-tester

Request an OAuth2 `client_credentials` token from Auth0, Entra ID, Keycloak, Okta or Ping,
print it on a single line, and show the decoded JWT.

- Credentials are **never stored by the tool**. Each setting is read from an environment variable or a `.env` file you provide;
  if unset you are prompted (secrets via `getpass`, not echoed).
- The token is **never written to disk**.
- Decoding is **unverified** by default; add `--verify` to check the signature against the IdP's JWKS.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

```bash
idp-m2m                 # menu
idp-m2m --idp okta
idp-m2m --idp entra --verify
python -m idp_m2m_token_tester --idp auth0
```

Prefer prompting or a secrets manager over exporting secrets in your shell history.

## Environment variables

| IdP | Variables (optional in parentheses) |
|---|---|
| Auth0 | `AUTH0_DOMAIN`, `AUTH0_CLIENT_ID`, `AUTH0_CLIENT_SECRET`, `AUTH0_AUDIENCE`, (`AUTH0_SCOPE`) |
| Entra | `ENTRA_TENANT_ID`, `ENTRA_CLIENT_ID`, `ENTRA_CLIENT_SECRET`, (`ENTRA_SCOPE`, default `api://<client_id>/.default`) |
| Keycloak | `KC_BASE`, `KC_REALM`, `KC_CLIENT_ID`, `KC_CLIENT_SECRET`, (`KC_SCOPE`) |
| Okta | `OKTA_DOMAIN`, `OKTA_CLIENT_ID`, `OKTA_CLIENT_SECRET`, `OKTA_SCOPE`, (`OKTA_AUTH_SERVER` default `default`, or `org`; `OKTA_AUTH_METHOD`) |
| Ping | `PING_FLAVOR` (`pingone` default / `pingfederate`), `PING_CLIENT_ID`, `PING_CLIENT_SECRET`, (`PING_SCOPE`, `PING_AUTH_METHOD`); PingOne: `PING_ENV_ID`, (`PING_REGION` default `com`); PingFederate: `PING_HOST` |

`*_AUTH_METHOD` is `client_secret_post` (default) or `client_secret_basic`. `private_key_jwt` is not supported.

## Using a `.env` file (convenient, but risky)

The tool reads a `.env` file directly. It looks for `./.env` automatically, or you can pass `--env-file PATH`.
Precedence for each setting: **real environment variable, then `.env` file, then prompt**.
Values from the file are held in memory only; they are not exported to your shell or written anywhere.

1. Copy the starter file [.env.example](.env.example) to `.env` in the folder you run the tool from and keep only
   the section for the IdP you need. Example of the result:

   ```dotenv
   OKTA_DOMAIN=dev-123456.okta.com
   OKTA_CLIENT_ID=0oa1b2c3d4e5f6g7h8i9
   OKTA_CLIENT_SECRET=your-secret-here
   OKTA_SCOPE=access_token
   ```

2. Restrict it to your user and run the tool (the tool warns if the file is readable by others):

   ```bash
   chmod 600 .env
   idp-m2m --idp okta
   idp-m2m --idp okta --env-file ~/secrets/okta-test.env
   ```

   Omit `*_CLIENT_SECRET` from the file to be prompted for it instead. An explicit `--env-file` that does not
   exist is an error; a missing default `./.env` is silently ignored.

### Danger: a `.env` file stores secrets in plaintext

The tool never writes the file, but keeping secrets in it undoes the "credentials are never stored" goal. Anyone or anything that can read the file gets a
working client secret.

- **Source control:** committing it, even once, leaks the secret permanently through git history. `.gitignore`
  here excludes `.env` and `.env.*`, but that protects only this repo. Never `git add -f` it.
- **Other exposure:** backups, cloud-synced folders (iCloud, OneDrive, Dropbox), screen shares, support bundles,
  and other tools or malware running as your user can read it.
- **Real client secrets are credentials:** a leaked M2M secret lets someone mint tokens as your application until it
  is rotated. Use test or non-production clients, and rotate the secret if the file is ever exposed.
- **Safer alternatives:** let the tool prompt you (the default), or pull values from a secrets manager or keychain
  at run time. Delete `.env` when you no longer need it.

## Setting environment variables in PyCharm

PyCharm passes these to the process it launches, so they are never stored in your shell.

1. Run the tool once so a run configuration exists. For example, create a **Python** configuration with
   **Module name** `idp_m2m_token_tester` and **Parameters** `--idp okta`. Make sure the project interpreter is
   this folder's `.venv`.
2. Open **Run | Edit Configurations...** and select that configuration.
3. Click the **Environment variables** field's folder/edit icon (or press `Shift+Enter` in the field).
4. Click **+** and add each name/value pair, such as `OKTA_DOMAIN`, `OKTA_CLIENT_ID` and `OKTA_SCOPE`. Click **OK**, then **Apply**.
5. Leave `*_CLIENT_SECRET` **unset** to be prompted. The prompt appears in the **Run** tool window.
   For `getpass` to work there, tick **Emulate terminal in output console** in the configuration.
   If you would rather run from the PyCharm **Terminal** tab, just run `idp-m2m` there; a `.env` in the project folder is picked up automatically.

Optional: PyCharm's **EnvFile** plugin (or the built-in `.env` file support in newer versions) can load a `.env`
file into a run configuration. The same plaintext-secret dangers apply.

Be aware that run configurations are stored in `.idea/` (for example `.idea/workspace.xml` or
`.idea/runConfigurations/`), so **any value you type into the Environment variables field is saved to disk in
plaintext** and can be committed if `.idea/` is not ignored. Keep secrets out of that field, and add `.idea/` to
`.gitignore` if you use PyCharm with this project.

## Layout

```
src/idp_m2m_token_tester/
  cli.py          argparse, IdP menu, orchestration
  config.py       env-var-then-prompt resolver
  jwt_decoder.py  unverified decode, optional JWKS verify, time claims
  display.py      output
  models.py  errors.py
  providers/      base.py (abstract IdpProvider) + one module per IdP
tests/            pytest, HTTP mocked with `responses`
```

Add an IdP by subclassing `IdpProvider` and registering it in `providers/__init__.py`.

## Development

```bash
pytest && ruff check . && mypy
```

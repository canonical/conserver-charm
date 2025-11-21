# Conserver Charm

[![Charmhub][charmhub-badge]][charmhub-site]
[![Test][test-badge]][test-site]
[![uv status][uv-badge]][uv-site]
[![Ruff status][ruff-badge]][ruff-site]

**Conserver Charm** is a charm that deploys and manages **[conserver]**, a
serial console management server. Conserver allows multiple users to watch a
serial console at the same time.

## Basic Usage

Conserver Charm is available on all major Linux distributions.

On [Juju-ready][juju] systems, you can deploy it on the command-line with:

```shell
juju deploy conserver
```

> [!NOTE]
> The charm automatically enables the `conserver-server` deb package,
> but you have to configure the charm to add connections, credentials, etc in order to properly start the service.

Then configure your deployment:

```shell
juju config conserver config-file="$(cat your-conserver.cf | base64 -w0)"
juju config conserver passwd-file="$(cat your-conserver.passwd | base64 -w0)"
```

## Configuration

- `config-file`: The **base64 encoded** contents for the conserver configuration
  file (i.e., `conserver.cf`). This file defines console access permissions,
  console device settings, logging configurations, server behavior settings, etc.
  Refer to the [`conserver.cf` documentation][conserver.cf] for more information.

- `passwd-file`: The **base64 encoded** contents for the conserver password file
  (i.e., `conserver.passwd`). This file controls user access to consoles.
  Refer to the [`conserver.passwd` documentation][conserver.passwd] for more
  information.

[charmhub-badge]: https://charmhub.io/conserver/badge.svg
[charmhub-site]: https://charmhub.io/conserver
[test-badge]: https://github.com/canonical/conserver-charm/actions/workflows/test.yaml/badge.svg
[test-site]: https://github.com/canonical/conserver-charm/actions/workflows/test.yaml
[uv-badge]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json
[uv-site]: https://github.com/astral-sh/uv
[ruff-badge]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
[ruff-site]: https://github.com/astral-sh/ruff
[conserver]: https://conserver.com/
[juju]: https://canonical.com/juju
[conserver.cf]: https://conserver.com/docs/conserver.cf.man.html
[conserver.passwd]: https://conserver.com/docs/conserver.passwd.man.html

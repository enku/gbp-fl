"""Tests for the `gbp fl fetch` sub-sub-command"""

# pylint: disable=missing-docstring
import argparse
from typing import Any
from unittest.mock import ANY, MagicMock, patch

from unittest_fixtures import TestCase, requires

from gbp_fl.cli import fetch

from .utils import cd


@requires("console", "tmpdir", gbp="gbp_client")
@patch("gbp_fl.cli.fetch.requests")
class HandlerTests(TestCase):
    options = {"records_backend": "memory"}

    def test(self, requests: MagicMock) -> None:
        args = argparse.Namespace(pkgspec="lighthouse/34/app-shells/bash-5.2_p37-1")
        gbp = self.fixtures.gbp
        console = self.fixtures.console
        pkg = "bash-5.2_p37-1"

        # This is a redirect that we let requests handle for us, so the requested URL
        # and the response URL will be different
        request_url = (
            "http://gbp.invalid/machines/lighthouse/builds/34/packages"
            f"/app-shells/bash/{pkg}"
        )
        response_url = (
            f"http://gbp.invalid/binpkgs/lighthouse.34/app-shells/bash/{pkg}.gpkg.tar"
        )

        mock_response = get_mock_response(url=response_url)

        requests.get.return_value = mock_response

        console.out.print(f"$ gbp fl fetch {args.pkgspec}")
        with cd(self.fixtures.tmpdir):
            status = fetch.handler(args, gbp, console)

        self.assertEqual(0, status)
        self.assertEqual("", console.err.file.getvalue())
        self.assertEqual(
            f"$ gbp fl fetch {args.pkgspec}\n" f"package saved as {pkg}.gpkg.tar\n",
            console.out.file.getvalue(),
        )

        with open(self.fixtures.tmpdir / f"{pkg}.gpkg.tar", "rb") as fp:
            content = fp.read()
        self.assertEqual(content, b"no matter")

        requests.get.assert_called_once_with(request_url, stream=True, timeout=ANY)

    def test_invalid_spec(self, requests: MagicMock) -> None:
        pkgspec = "lighthouse/34/bash-5.2_p37-1"
        args = argparse.Namespace(pkgspec=pkgspec)
        gbp = MagicMock()
        console = self.fixtures.console

        with cd(self.fixtures.tmpdir):
            status = fetch.handler(args, gbp, console)

        self.assertEqual(status, 1)
        self.assertEqual(f"Invalid specifier: {pkgspec}\n", console.err.file.getvalue())
        self.assertEqual("", console.out.file.getvalue())

        requests.get.assert_not_called()

    def test_when_server_returns_404(self, requests: MagicMock) -> None:
        pkgspec = "lighthouse/34/app-shells/bash-5.2_p37-1"
        args = argparse.Namespace(pkgspec=pkgspec)
        url = (
            "http://gbp.invalid/machines/lighthouse/builds/34/packages"
            "/app-shells/bash/bash-5.2_p37-1"
        )
        mock_response = get_mock_response(404, b"Not Found", url=url)
        gbp = self.fixtures.gbp
        console = self.fixtures.console
        requests.get.return_value = mock_response

        with cd(self.fixtures.tmpdir):
            status = fetch.handler(args, gbp, console)

        self.assertEqual(2, status)
        self.assertEqual(
            "The requested package was not found.\n", console.err.file.getvalue()
        )


class ParseArgsTests(TestCase):
    def test(self) -> None:
        parser = argparse.ArgumentParser()
        fetch.parse_args(parser)


def get_mock_response(
    status_code: int = 200, content: bytes = b"no matter", **attrs: Any
) -> MagicMock:
    mock_response = MagicMock(status_code=status_code)
    mock_response.iter_content.return_value = iter([content])
    for name, value in attrs.items():
        setattr(mock_response, name, value)

    mock_ctx = MagicMock()
    mock_ctx.__enter__.return_value = mock_response

    return mock_ctx

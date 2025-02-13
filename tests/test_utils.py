"""Tests for gbp_fl.utils"""

from unittest_fixtures import TestCase

from gbp_fl.utils import Parsed, parse_pkgspec

# pylint: disable=missing-docstring


class ParsePkgspecTests(TestCase):
    def test_host_with_dash(self) -> None:
        parsed = parse_pkgspec("jenkins-python/211/dev-python/anyio-4.8.0-1")

        self.assertIsNotNone(parsed)

        self.assertEqual(
            Parsed(
                machine="jenkins-python",
                build_id="211",
                c="dev-python",
                p="anyio",
                v="4.8.0",
                b=1,
            ),
            parsed,
        )

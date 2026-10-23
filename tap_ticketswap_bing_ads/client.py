"""Shared client and base stream for tap-ticketswap-bing-ads.

The Bing Ads (Microsoft Advertising) API is SOAP-based, so these streams wrap
the official ``bingads`` SDK rather than using the Singer SDK's REST helpers.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

import bingads.exceptions
from bingads.authorization import AuthorizationData, OAuthWebAuthCodeGrant
from bingads.service_client import ServiceClient
from singer_sdk.streams import Stream

if TYPE_CHECKING:
    from singer_sdk.helpers.types import Context

    from tap_ticketswap_bing_ads.tap import TapBingAds

API_VERSION = 13


class BingAdsStream(Stream):
    """Base stream that authenticates once and iterates over the configured accounts."""

    #: Bing Ads service used by the stream, e.g. ``"CampaignManagementService"``.
    service_name: str

    def __init__(self, tap: TapBingAds) -> None:
        """Initialise the stream and reset the cached authentication."""
        super().__init__(tap)
        self._authentication: OAuthWebAuthCodeGrant | None = None

    @property
    def account_ids(self) -> list[str]:
        """Return the configured account ids as a list of strings."""
        raw = self.config["account_ids"]
        if isinstance(raw, str):
            return [part.strip() for part in raw.split(",") if part.strip()]
        return [str(part) for part in raw]

    def _get_authentication(self) -> OAuthWebAuthCodeGrant:
        """Exchange the refresh token for OAuth tokens (cached per stream).

        Falls back to the legacy ``bingads.manage`` scope when the default
        (no scope) request is rejected, matching the behaviour of the source.
        """
        if self._authentication is not None:
            return self._authentication

        client_id = self.config["oauth_client_id"]
        client_secret = self.config["oauth_client_secret"]
        refresh_token = self.config["refresh_token"]

        try:
            authentication = OAuthWebAuthCodeGrant(client_id, client_secret, "")
            authentication.request_oauth_tokens_by_refresh_token(refresh_token)
        except bingads.exceptions.OAuthTokenRequestException:
            authentication = OAuthWebAuthCodeGrant(
                client_id, client_secret, "", oauth_scope="bingads.manage"
            )
            authentication.request_oauth_tokens_by_refresh_token(refresh_token)

        self._authentication = authentication
        return authentication

    def authorization_data(self, account_id: str) -> AuthorizationData:
        """Build the ``AuthorizationData`` for a single account."""
        return AuthorizationData(
            account_id=account_id,
            customer_id=self.config["customer_id"],
            developer_token=self.config["developer_token"],
            authentication=self._get_authentication(),
        )

    def service_client(self, account_id: str) -> ServiceClient:
        """Return a SOAP ``ServiceClient`` for ``self.service_name`` and account."""
        return ServiceClient(
            service=self.service_name,
            version=API_VERSION,
            authorization_data=self.authorization_data(account_id),
        )

    def post_process(self, row: dict, context: Context | None = None) -> dict | None:  # noqa: ARG002
        """Coerce raw string values from the report CSV to their schema types."""
        for key, prop in self.schema.get("properties", {}).items():
            if key not in row:
                continue
            value = row[key]
            if isinstance(value, str):
                value = value.strip()
            if value in ("", None):
                row[key] = None
                continue
            types = prop.get("type", [])
            if isinstance(types, str):
                types = [types]
            if "integer" in types:
                row[key] = 0 if value == "--" else int(str(value).replace(",", ""))
            elif "number" in types:
                row[key] = (
                    0.0 if value == "--" else float(str(value).replace("%", "").replace(",", ""))
                )
            elif prop.get("format") == "date" and not isinstance(value, date):
                row[key] = _parse_date(str(value))
            else:
                row[key] = value
        return row


def _parse_date(value: str) -> str:
    """Parse a Bing report date into an ISO ``YYYY-MM-DD`` string."""
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc).date().isoformat()
        except ValueError:
            continue
    return value

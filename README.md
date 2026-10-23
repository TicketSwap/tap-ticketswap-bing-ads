# tap-ticketswap-bing-ads

`tap-ticketswap-bing-ads` is a Singer tap for Microsoft (Bing) Ads, built with
the [Meltano Singer SDK](https://sdk.meltano.com).

It is a slimmed-down replacement for the legacy
[`tap-bing-ads`](https://github.com/TicketSwap/tap-bing-ads) and only extracts
the two streams consumed by the `microsoft_ads` dbt models:

| Stream | Source service | Replication |
|---|---|---|
| `campaigns` | Campaign Management | Full table |
| `campaign_performance_report` | Reporting (daily) | Incremental on `TimePeriod` |

Field names are emitted in the API's PascalCase form so that, once lower-cased
by the loader, the warehouse columns are identical to the previous tap — no dbt
changes are required.

## Configuration

| Setting | Required | Description |
|---|---|---|
| `developer_token` | yes | Microsoft Advertising developer token. |
| `oauth_client_id` | yes | Azure application (client) id. |
| `oauth_client_secret` | yes | Azure application client secret. |
| `refresh_token` | yes | OAuth refresh token. |
| `customer_id` | yes | Manager (customer) id. |
| `account_ids` | yes | Comma-separated list of account ids. |
| `start_date` | yes | Earliest report date (`YYYY-MM-DDTHH:MM:SSZ`). |
| `conversion_window` | no | Days before the bookmark to re-sync (default 30). |
| `report_max_days` | no | Max days per report call (default 30). |

A full list of settings is available by running:

```bash
tap-ticketswap-bing-ads --about
```

Config values are read from matching `TAP_TICKETSWAP_BING_ADS_*` environment
variables (see `.env.example`) when `--config=ENV` is passed.

## Usage

```bash
tap-ticketswap-bing-ads --version
tap-ticketswap-bing-ads --config CONFIG --discover > ./catalog.json
tap-ticketswap-bing-ads --config CONFIG --catalog ./catalog.json
```

## Developer Resources

Prerequisites: Python 3.10–3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run pytest tests/test_core.py
uv run tap-ticketswap-bing-ads --help
```

`uv run pytest` also runs the SDK's standard tap tests against the API, which need
the `TAP_TICKETSWAP_BING_ADS_*` credentials from `.env.example`.

### Testing with [Meltano](https://www.meltano.com)

```bash
uv tool install meltano
meltano invoke tap-ticketswap-bing-ads --version
meltano run tap-ticketswap-bing-ads target-jsonl
```

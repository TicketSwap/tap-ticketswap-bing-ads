"""Schema definitions for tap-ticketswap-bing-ads streams.

Field names are kept in the PascalCase form returned by the Bing Ads API so
that, once lower-cased by the loader, the warehouse columns match those already
in the ``microsoft_ads`` schema. Only the columns consumed by the downstream
dbt models are declared here.
"""

from __future__ import annotations

from singer_sdk import typing as th

# stg_microsoft_ads__campaigns reads: Id, Name, Status
CAMPAIGNS = th.PropertiesList(
    th.Property("Id", th.IntegerType, description="Campaign identifier."),
    th.Property("Name", th.StringType, description="Campaign name."),
    th.Property("Status", th.StringType, description="Campaign status."),
).to_dict()

# stg_microsoft_ads__campaign_performance reads: CampaignId, DeviceType, Network,
# Impressions, Clicks, Ctr, AverageCpc, AverageCpm, Spend, TimePeriod.
CAMPAIGN_PERFORMANCE_REPORT = th.PropertiesList(
    th.Property("TimePeriod", th.DateType, description="Day the metrics apply to."),
    th.Property("CampaignId", th.StringType, description="Campaign identifier."),
    th.Property("DeviceType", th.StringType, description="Device the metrics were served on."),
    th.Property("Network", th.StringType, description="Ad network the metrics were served on."),
    th.Property("Impressions", th.IntegerType, description="Number of impressions."),
    th.Property("Clicks", th.IntegerType, description="Number of clicks."),
    th.Property("Ctr", th.NumberType, description="Click-through rate (percent)."),
    th.Property("AverageCpc", th.NumberType, description="Average cost per click."),
    th.Property("AverageCpm", th.NumberType, description="Average cost per thousand impressions."),
    th.Property("Spend", th.NumberType, description="Amount spent."),
).to_dict()

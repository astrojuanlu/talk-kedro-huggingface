"""
This is a boilerplate pipeline 'data_extraction'
generated using Kedro 0.18.14
"""
from __future__ import annotations

import datetime as dt
import json

import polars as pl
import structlog
from pydantic import BaseModel, ConfigDict, TypeAdapter

logger = structlog.get_logger()


class MastodonAccount(BaseModel):
    model_config = ConfigDict(strict=True)

    id: str
    username: str
    acct: str
    display_name: str


class MastodonMention(BaseModel):
    model_config = ConfigDict(strict=True)

    id: str
    username: str
    acct: str


class MastodonTag(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str
    url: str


class MastodonStatus(BaseModel):
    model_config = ConfigDict(strict=True)

    id: str
    uri: str
    created_at: dt.datetime
    in_reply_to_id: str | None
    sensitive: bool
    spoiler_text: str
    visibility: str
    language: str | None
    url: str
    content: str
    account: MastodonAccount
    mentions: list[MastodonMention]
    reblogs_count: int
    favourites_count: int
    replies_count: int
    # reblog: "MastodonStatus"  # Unused

    # FIXME: # Might be empty, which is problematic when serializing to Delta
    # tags: list[MastodonTag]


def extract_statuses(statuses_gen, df_statuses, absolute_min_id) -> pl.DataFrame:
    if len(df_statuses) > 0:
        latest_id = (
            df_statuses.filter(pl.col("created_at") == pl.col("created_at").max())
            .select(pl.col("id"))
            .item()
        )
    else:
        latest_id = absolute_min_id

    # Pump generator before sending the first value
    next(statuses_gen)
    try:
        statuses = [statuses_gen.send(latest_id)]
    except StopIteration:
        return pl.DataFrame([], schema=df_statuses.schema)

    statuses.extend(statuses_gen)
    logger.debug("Extracted statuses", num_statuses=len(statuses), latest_id=latest_id)

    adapter = TypeAdapter(list[MastodonStatus])
    objects = adapter.validate_json(json.dumps(statuses))
    return pl.from_dicts(objects)

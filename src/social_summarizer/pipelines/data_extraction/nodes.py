"""
This is a boilerplate pipeline 'data_extraction'
generated using Kedro 0.18.14
"""
from __future__ import annotations

import datetime as dt
import json
import typing as t

import polars as pl
from pydantic import BaseModel, ConfigDict, TypeAdapter


class MastodonAccount(BaseModel):
    model_config = ConfigDict(strict=True)

    id: str
    username: str
    acct: str


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

    # FIXME: # Might be empty, which is problematic when serializing to Delta
    # tags: list[MastodonTag]


def extract_statuses(statuses: list[dict[str, t.Any]]) -> pl.DataFrame:
    adapter = TypeAdapter(list[MastodonStatus])
    objects = adapter.validate_json(json.dumps(statuses))
    return pl.from_dicts(objects)

"""
This is a boilerplate pipeline 'data_cleaning'
generated using Kedro 0.18.14
"""

import polars as pl
from bs4 import BeautifulSoup


def clean_statuses(df: pl.DataFrame) -> pl.DataFrame:
    df_clean = df.select(
        pl.col("id", "created_at", "content"),
        pl.col("account").struct.field("acct").alias("acct"),
        pl.col("mentions").list.eval(pl.element().struct.field("acct")),
    ).filter(pl.col("content") != "")

    df_clean = df_clean.with_columns(
        pl.col("content")
        .map_elements(
            lambda content: BeautifulSoup(content, features="html.parser").get_text()
        )
        .str.replace_all(r"@[\w@\.]+ ", "")
        .str.replace_all(r"http\S+", "")
        .alias("text")
    )

    return df_clean

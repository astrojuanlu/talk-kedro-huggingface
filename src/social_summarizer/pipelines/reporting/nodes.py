"""
This is a boilerplate pipeline 'reporting'
generated using Kedro 0.18.14
"""

from textwrap import fill

import polars as pl
from transformers.pipelines.base import Pipeline as HFPipeline


def write_executive_summary(
    statuses: pl.DataFrame, model: HFPipeline, max_num_statuses: int
) -> str:
    statuses_text = statuses.head(max_num_statuses)["text"].to_list()
    short_prompt = """
    This is a list of posts that Luis Villa posted this week on Mastodon:

    {}
    """.format("\n\n".join([f"{post}" for post in statuses_text]))

    executive_summary_results = model(short_prompt)

    return fill(executive_summary_results[0]["summary_text"])

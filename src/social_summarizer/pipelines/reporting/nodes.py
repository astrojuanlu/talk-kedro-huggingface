"""
This is a boilerplate pipeline 'reporting'
generated using Kedro 0.18.14
"""

from textwrap import fill

import polars as pl
from transformers.pipelines.base import Pipeline as HFPipeline


def get_hashtags(df: pl.DataFrame, mask_filler, max_number_statuses: int) -> list[str]:
    posts = df["text"].head(max_number_statuses).to_list()
    results = mask_filler([post + " #<mask>" for post in posts])

    hashtags = set()
    for ht_list in results:
        for hashtag in ht_list:
            hashtags.add(hashtag["token_str"])

    return list(hashtags)


def write_executive_summary(
    statuses: pl.DataFrame, summarizer: HFPipeline, max_num_statuses: int
) -> str:
    statuses_text = statuses.head(max_num_statuses)["text"].to_list()
    short_prompt = """
    This is a list of posts:

    {}
    """.format("\n\n".join(post for post in statuses_text))
    executive_summary_results = summarizer(short_prompt)

    return fill(executive_summary_results[0]["summary_text"])


def consolidate_report(hashtags, summary):
    report = f"""List of topics: {hashtags[:5]}

    Summary:

    {summary}
    """
    return report

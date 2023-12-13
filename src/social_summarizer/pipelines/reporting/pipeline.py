"""
This is a boilerplate pipeline 'reporting'
generated using Kedro 0.18.14
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import consolidate_report, get_hashtags, write_executive_summary


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=get_hashtags,
                inputs=[
                    "statuses_clean",
                    "fill_mask_model",
                    "params:reporting.max_num_statuses",
                ],
                outputs="hashtags_list",
            ),
            node(
                func=write_executive_summary,
                inputs=[
                    "statuses_clean",
                    "cnn.summarizer_model",
                    "params:reporting.max_num_statuses",
                ],
                outputs="summary_text",
            ),
            node(
                func=consolidate_report,
                inputs=["hashtags_list", "summary_text"],
                outputs="executive_summary",
            ),
        ]
    )

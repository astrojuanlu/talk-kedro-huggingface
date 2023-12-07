"""
This is a boilerplate pipeline 'data_extraction'
generated using Kedro 0.18.14
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import extract_statuses


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=extract_statuses,
                inputs=[
                    "raw_statuses",
                    "statuses_table_readonly",
                    "params:absolute_min_id",
                ],
                outputs="statuses_table",
            ),
        ]
    )

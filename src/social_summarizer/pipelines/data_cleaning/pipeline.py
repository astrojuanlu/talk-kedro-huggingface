"""
This is a boilerplate pipeline 'data_cleaning'
generated using Kedro 0.18.14
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import clean_statuses


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=clean_statuses,
                inputs="statuses_table",
                outputs="statuses_clean",
            )
        ]
    )

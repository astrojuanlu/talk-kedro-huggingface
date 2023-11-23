"""
This is a boilerplate pipeline 'reporting'
generated using Kedro 0.18.14
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import write_executive_summary


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=write_executive_summary,
                inputs=[
                    "statuses_clean",
                    "cnn.summarizer_model",
                    "params:reporting.max_num_statuses",
                ],
                outputs="executive_summary",
            )
        ]
    )

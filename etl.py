# "Manual" pipeline to workaround some time limits

from urllib.parse import parse_qsl, urljoin, urlparse

import httpx
import polars as pl
import structlog
from deltalake.exceptions import TableNotFoundError
from kedro.config import OmegaConfigLoader
from kedro.io import DataCatalog
from social_summarizer.pipelines.data_extraction.nodes import extract_statuses

BASE_MASTODON_URL = "https://{instance_domain}/api/v1/"
STATUSES_ENDPOINT = "accounts/{account_id}/statuses/"

logger = structlog.get_logger()


def parse_links(links_str: str) -> dict[str, str]:
    links_str_list = links_str.split(", ")

    links = {}
    for link_str in links_str_list:
        url_str, rel_str = link_str.split("; ")
        rel_value = rel_str.removeprefix('rel="').removesuffix('"')
        links[rel_value] = url_str.removeprefix("<").removesuffix(">")

    return links


def get_statuses(
    instance_domain, account_id, *, start_id=None, max_id=None, max_requests=10
):
    client = httpx.Client()

    url = urljoin(BASE_MASTODON_URL, STATUSES_ENDPOINT).format(
        instance_domain=instance_domain,
        account_id=account_id,
    )

    params = {}
    if max_id is not None:
        # Set an upper bound
        params["max_id"] = max_id
    if start_id is None:
        # Take <limit> statuses into the past starting from max_id
        pass
    else:
        # Set a cursor in the status immediately newer than start_id
        # and paginate from there
        params["min_id"] = start_id

    statuses = []
    for _ in range(max_requests):
        response = client.get(url, params=params)
        if not response.is_success:
            logger.error(
                "Error occurred in the last request",
                status_code=response.status_code,
                content=response.content,
            )
            break

        # Extend list of statuses and crop it to its maximum length,
        # keeping the earliest ones
        statuses = response.json() + statuses

        if link_header_str := response.headers.get("link"):
            links = parse_links(link_header_str)
            if "prev" in links:
                prev_url_obj = urlparse(links["prev"])
                params.update(dict(parse_qsl(prev_url_obj.query)))
                url = prev_url_obj._replace(query="").geturl()
            else:
                # No more statuses
                break
    else:
        logger.warning("Max number of requests reached")

    return statuses


def main(instance_domain, account_id, latest_id=None):
    conf_loader = OmegaConfigLoader(
        conf_source="conf", base_env="base", default_run_env="local"
    )
    catalog = DataCatalog.from_config(
        conf_loader.get("catalog"), credentials=conf_loader.get("credentials")
    )

    if latest_id is None:
        try:
            df_statuses = catalog.load("statuses_table")

            latest_id = (
                df_statuses.filter(pl.col("created_at") == pl.col("created_at").max())
                .select(pl.col("id"))
                .item()
            )
        except TableNotFoundError:
            pass

    statuses = get_statuses(instance_domain, account_id, start_id=latest_id)
    if statuses:
        df_statuses = extract_statuses(statuses).sort("created_at")

        catalog.save("statuses_table", df_statuses)

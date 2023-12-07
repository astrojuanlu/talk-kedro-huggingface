import typing as t
from urllib.parse import parse_qsl, urljoin, urlparse

import httpx
import structlog
from kedro.io import AbstractDataset

logger = structlog.get_logger()

BASE_MASTODON_URL = "https://{instance_domain}/api/v1/"
STATUSES_ENDPOINT = "accounts/{account_id}/statuses/"


def parse_links(links_str: str) -> dict[str, str]:
    links_str_list = links_str.split(", ")

    links = {}
    for link_str in links_str_list:
        url_str, rel_str = link_str.split("; ")
        rel_value = rel_str.removeprefix('rel="').removesuffix('"')
        links[rel_value] = url_str.removeprefix("<").removesuffix(">")

    return links


def get_statuses(
    instance_domain,
    account_id,
    *,
    max_id=None,
    max_requests=10,
    client=None,
    base_mastodon_url=BASE_MASTODON_URL,
    statuses_endpoint=STATUSES_ENDPOINT,
):
    if not client:
        client = httpx.Client()

    url = urljoin(base_mastodon_url, statuses_endpoint).format(
        instance_domain=instance_domain,
        account_id=account_id,
    )

    start_id = yield

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

    for _ in range(max_requests):
        response = client.get(url, params=params)
        if not response.is_success:
            logger.error(
                "Error occurred in the last request",
                status_code=response.status_code,
                content=response.content,
            )
            break

        yield from response.json()

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
            # No more statuses
            break
    else:
        logger.warning("Max number of requests reached")


class MastodonStatusesDataset(AbstractDataset):
    def __init__(
        self,
        instance_domain,
        account_id,
        max_requests=10,
    ):
        self.instance_domain = instance_domain
        self.account_id = account_id
        self.max_requests = max_requests

        self._client = httpx.Client()

    def _load(self) -> t.Generator[t.Dict[str, t.Any], str, None]:
        return get_statuses(
            instance_domain=self.instance_domain,
            account_id=self.account_id,
            max_requests=self.max_requests,
            client=self._client,
        )

    def _save(self, data) -> None:
        raise NotImplementedError(
            f"Save is not implemented for {self.__class__.__name__}"
        )

    def _describe(self) -> t.Dict[str, t.Any]:
        return dict(
            instance_domain=self.instance_domain,
            account_id=self.account_id,
            max_requests=self.max_requests,
        )

"""
Proxy server for Stoplight Prism with response example selection logic.

Adapted from https://stackoverflow.com/a/36601467
"""

import logging
import os
import sys

import requests  # pyright: ignore [reportMissingModuleSource]
from flask import Flask, Request, Response, request  # pyright: ignore [reportMissingImports]

# Configure logging to output to stdout
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# HTTP proxy to Prism
UPSTREAM_HOST = os.environ.get("UPSTREAM_HOST")
if not UPSTREAM_HOST:
    NO_UPSTREAM_HOST = "UPSTREAM_HOST environment variable not set"
    raise ValueError(NO_UPSTREAM_HOST)

app = Flask(__name__)
app.logger.setLevel("INFO")
session = requests.Session()

HOP_BY_HOP_HEADERS = [
    "connection",
    "content-encoding",
    "content-length",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
]

PATIENT_EXAMPLES = {
    "patient-check/50000000001": "example_50000000001",
    "patient-check/50000000002": "example_50000000002",
    "patient-check/50000000003": "example_50000000003",
    "patient-check/50000000004": "example_50000000004",
    "patient-check/50000000005": "example_50000000005",
    "patient-check/50000000006": "example_50000000006",
    "patient-check/50000000007": "example_50000000007",
    "patient-check/50000000008": "example_50000000008",
    "patient-check/50000000009": "example_50000000009",
    "patient-check/50000000010": "example_50000000010",
    "patient-check/50000000011": "example_50000000011",
    "patient-check/50000000012": "example_50000000012",
    "patient-check/50000000013": "example_50000000013",
    "patient-check/50000000014": "example_50000000014",
    "patient-check/9686368973": "example_5000000001",
    "patient-check/9686368906": "example_5000000002",
    "patient-check/9658218873": "example_5000000003",
    "patient-check/9658218881": "example_5000000004",
    "patient-check/9658218903": "example_5000000005",
    "patient-check/9658218989": "example_5000000006",
    "patient-check/9658218997": "example_5000000007",
    "patient-check/9658219004": "example_5000000008",
    "patient-check/9658219012": "example_5000000009",
    "patient-check/9658220142": "example_5000000010",
    "patient-check/9658220150": "example_5000000011",
    "patient-check/9450114080": "example_5000000012",
    "patient-check/9466447939": "example_5000000013",
    "patient-check/9657933617": "example_5000000014",    
    "patient-check/90000000400": "code400",
    "patient-check/90000000404": "code404",
    "patient-check/90000000422": "code422",
    "patient-check/90000000500": "code500",
}


def exclude_hop_by_hop(headers: dict) -> list[tuple[str, str]]:
    """
    Exclude hop-by-hop headers, which are meaningful only for a single
    transport-level connection, and are not stored by caches or forwarded by
    proxies. See https://www.rfc-editor.org/rfc/rfc2616#section-13.5.1.
    """
    return [(k, v) for k, v in headers.items() if k.lower() not in HOP_BY_HOP_HEADERS]


def get_prism_prompt_for_example(patient_examples: dict, request: Request) -> str | None:
    """
    Given the whole request, return the `Prefer:` header value if a specific
    example is desired. Otherwise, return `None`.
    """
    for patient_id, example in patient_examples.items():
        if patient_id in request.full_path:
            return example
    return None


def parse_prefer_header_value(prefer_header_value: str) -> str:
    """
    Parse the Prefer header value to extract the example name.
    """
    if prefer_header_value.startswith("example"):
        return f"example={prefer_header_value}"
    if prefer_header_value.startswith("code"):
        return f"code={prefer_header_value[4:]}"
    return ""


@app.route("/_status", methods=["GET"])
def health_check() -> Response:
    """
    Health-check endpoint to verify the application is running.
    Returns a 200 OK status with a simple JSON response.
    """
    return Response('{"status": "ok"}', status=200, mimetype="application/json")


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def proxy_to_upstream(path: str) -> Response:  # noqa: ARG001
    headers_to_upstream = {k: v for k, v in request.headers if k.lower() != "host"}

    prefer_header_value = get_prism_prompt_for_example(PATIENT_EXAMPLES, request)
    if prefer_header_value:
        headers_to_upstream["prefer"] = parse_prefer_header_value(prefer_header_value)

    request_to_upstream = requests.Request(
        method=request.method,
        url=request.url.replace(request.host_url, UPSTREAM_HOST + "/"),  # pyright: ignore [reportOptionalOperand]
        headers=headers_to_upstream,
        data=request.get_data(),
        cookies=request.cookies,
    ).prepare()
    response_from_upstream = session.send(request_to_upstream)

    return Response(
        response_from_upstream.content,
        response_from_upstream.status_code,
        exclude_hop_by_hop(dict(response_from_upstream.raw.headers)),
    )

"""
Proxy server for Stoplight Prism with response example selection logic.

Adapted from https://stackoverflow.com/a/36601467
"""

import logging
import os
import sys
from http import HTTPStatus

import requests  # pyright: ignore [reportMissingModuleSource]
from flask import Flask, Request, Response, make_response, request  # pyright: ignore [reportMissingImports]

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
    "patient-check/5000000001": "example_50000000001",
    "patient-check/5000000002": "example_50000000002",
    "patient-check/5000000003": "example_50000000003",
    "patient-check/5000000004": "example_50000000004",
    "patient-check/5000000005": "example_50000000005",
    "patient-check/5000000006": "example_50000000006",
    "patient-check/5000000007": "example_50000000007",
    "patient-check/5000000008": "example_50000000008",
    "patient-check/5000000009": "example_50000000009",
    "patient-check/5000000010": "example_50000000010",
    "patient-check/5000000011": "example_50000000011",
    "patient-check/5000000012": "example_50000000012",
    "patient-check/5000000013": "example_50000000013",
    "patient-check/5000000014": "example_50000000014",
    "patient-check/5000000015": "example_50000000015",
    "patient-check/5000000016": "example_50000000016",
    "patient-check/5000000017": "example_50000000017",
    "patient-check/5000000018": "example_50000000018",
    "patient-check/5000000019": "example_50000000019",
    "patient-check/5000000020": "example_50000000020",
    "patient-check/5000000021": "example_50000000021",
    "patient-check/5000000022": "example_50000000022",
    "patient-check/5000000023": "example_50000000023",
    "patient-check/5000000024": "example_50000000024",
    # Incorrectly sized mock NHS Numbers (retained for backward compatabliity)
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
    "patient-check/50000000015": "example_50000000015",
    "patient-check/50000000016": "example_50000000016",
    "patient-check/50000000017": "example_50000000017",
    "patient-check/50000000018": "example_50000000018",
    "patient-check/50000000019": "example_50000000019",
    "patient-check/50000000020": "example_50000000020",
    "patient-check/50000000021": "example_50000000021",
    "patient-check/50000000022": "example_50000000022",
    "patient-check/50000000023": "example_50000000023",
    "patient-check/50000000024": "example_50000000024",
    # Support error scenario invocation
    "patient-check/90000000400": "code400",
    "patient-check/90000000404": "code404",
    "patient-check/90000000422": "code422",
    "patient-check/90000000500": "code500",
    # VitA Specific NHS Number Mapping
    "patient-check/9686368973": "example_50000000001",
    "patient-check/9735548852": "example_50000000001",
    "patient-check/9686368906": "example_50000000002",
    "patient-check/9658218873": "example_50000000003",
    "patient-check/9658218881": "example_50000000004",
    "patient-check/9735548844": "example_50000000004",
    "patient-check/9658218903": "example_50000000005",
    "patient-check/9658218989": "example_50000000006",
    "patient-check/9658218997": "example_50000000007",
    "patient-check/9658219004": "example_50000000008",
    "patient-check/9658219012": "example_50000000009",
    "patient-check/9658220142": "example_50000000010",
    "patient-check/9658220150": "example_50000000011",
    "patient-check/9450114080": "example_50000000012",
    "patient-check/9466447939": "example_50000000013",
    "patient-check/9657933617": "example_50000000014",
    "patient-check/9735549018": "example_50000000015",
    "patient-check/9735549026": "example_50000000016",
    "patient-check/9735549034": "example_50000000017",
    "patient-check/9735549042": "example_50000000018",
    "patient-check/9735549050": "example_50000000019",
    "patient-check/9735549069": "example_50000000020",
    "patient-check/9735549077": "example_50000000021",
    "patient-check/9735549085": "example_50000000022",
    "patient-check/9735549093": "example_50000000023",
    "patient-check/9735549107": "example_50000000024",
    "patient-check/9800878378": "code400",
    "patient-check/9661033404": "code404",
    "patient-check/9451019030": "code422",
    "patient-check/9436793375": "code500",
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


@app.route("/patient-check/_status", methods=["GET"])
def health_check() -> Response:
    """
    Health-check endpoint to verify the application is running.
    Returns a 200 OK status with a simple JSON response.
    """
    status_json = {
        "status": "pass",
        "version": "",
        "revision": "",
        "releaseId": "",
        "commitId": "",
        "checks": {
            "healthcheckService:status": [
                {
                    "status": "pass",
                    "timeout": False,
                    "responseCode": 200,
                    "outcome": "<html><h1>Ok</h1></html>",
                    "links": {"self": "https://default-eligibility-signposting-api-live/patient-check/_status"},
                }
            ]
        },
    }
    return make_response(status_json, HTTPStatus.OK, {"Content-Type": "application/json"})


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

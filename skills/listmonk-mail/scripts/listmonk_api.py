"""Read listmonk data and create lists/drafts; intentionally has no send command."""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate_url(url):
    parts = urllib.parse.urlsplit(url)
    if parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError("URL must not contain credentials, query parameters or fragments.")
    if not parts.hostname or parts.scheme not in ("http", "https"):
        raise ValueError("Set LISTMONK_URL to an HTTP(S) instance address.")
    if parts.scheme == "http" and parts.hostname.lower() not in ("localhost", "127.0.0.1", "::1"):
        raise ValueError("Remote instances require HTTPS.")
    return url.rstrip("/")


class Client:
    def __init__(self, url, user=None, token=None):
        self.url = validate_url(url)
        self.user, self.token = user, token
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def request(self, method, path, payload=None, authenticated=True):
        headers = {"Accept": "application/json"}
        if authenticated:
            if not self.user or not self.token:
                raise ValueError("Set LISTMONK_API_USER and LISTMONK_API_TOKEN privately on this machine.")
            credentials = base64.b64encode(f"{self.user}:{self.token}".encode()).decode()
            headers["Authorization"] = "Basic " + credentials
        data = None
        if payload is not None:
            headers["Content-Type"] = "application/json; charset=utf-8"
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(self.url + path, data=data, headers=headers, method=method)
        try:
            with self.opener.open(request, timeout=20) as response:
                if not authenticated:
                    return {"http_status": response.status, "api_authenticated": False}
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            # Error bodies can contain user data. Report only the status, never credentials.
            raise ValueError(f"HTTP {error.code}; check permissions, URL and server logs privately. No automatic retry.") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ValueError("Connection failed or timed out. Query current state before retrying a mutation.") from None


def draft_payload(source):
    allowed = {"name", "subject", "from_email", "lists", "body", "content_type",
               "template_id", "tags", "altbody", "headers"}
    if not isinstance(source, dict) or set(source) - allowed:
        raise ValueError("Draft contains unsupported fields (scheduling and sending are not accepted).")
    for key in ("name", "subject", "from_email", "body"):
        if not isinstance(source.get(key), str) or not source[key].strip():
            raise ValueError(f"Draft requires a nonempty {key} string.")
    if any(char in source["from_email"] for char in "\r\n"):
        raise ValueError("From address must not contain line breaks.")
    lists = source.get("lists")
    if not isinstance(lists, list) or not lists or any(type(item) is not int or item <= 0 for item in lists):
        raise ValueError("Draft requires positive integer list IDs.")
    if source.get("content_type", "html") not in ("html", "richtext", "markdown", "plain"):
        raise ValueError("Unsupported content type; use the UI for visual editor content.")
    if type(source.get("template_id")) is not int or source["template_id"] <= 0:
        raise ValueError("Specify an existing positive template_id.")
    result = dict(source)
    result.update(type="regular", messenger="email", content_type=source.get("content_type", "html"))
    return result


def execute(client, args):
    command = args.command
    if command == "health":
        return client.request("GET", "/", authenticated=False)
    if command in ("lists", "campaigns", "templates"):
        return client.request("GET", f"/api/{command}?page={args.page}&per_page=100")
    if command == "campaign":
        return client.request("GET", f"/api/campaigns/{args.id}")
    if command == "import-status":
        return client.request("GET", "/api/import/subscribers")
    if command == "create-list":
        if not args.name.strip():
            raise ValueError("List name cannot be empty.")
        return client.request("POST", "/api/lists", {"name": args.name, "type": "private",
                              "optin": args.optin, "tags": []})
    if command == "create-draft":
        payload = draft_payload(json.loads(Path(args.file).read_text(encoding="utf-8-sig")))
        response = client.request("POST", "/api/campaigns", payload)
        if response.get("data", {}).get("status") != "draft":
            raise ValueError("Unexpected campaign status; inspect the instance before further action.")
        return {"data": {key: response["data"].get(key) for key in
                          ("id", "name", "status", "subject", "from_email", "lists")}}
    raise ValueError("Unsupported operation.")


def positive(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("Must be positive.")
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("health")
    sub.add_parser("import-status")
    for name in ("lists", "campaigns", "templates"):
        sub.add_parser(name).add_argument("--page", type=positive, default=1)
    sub.add_parser("campaign").add_argument("id", type=positive)
    create = sub.add_parser("create-list")
    create.add_argument("name")
    create.add_argument("--optin", choices=("single", "double"), default="single")
    sub.add_parser("create-draft").add_argument("file")
    args = parser.parse_args()
    try:
        client = Client(os.environ.get("LISTMONK_URL", "http://127.0.0.1:9000"),
                        os.environ.get("LISTMONK_API_USER"), os.environ.get("LISTMONK_API_TOKEN"))
        print(json.dumps(execute(client, args), ensure_ascii=False, indent=2))
    except (ValueError, OSError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()

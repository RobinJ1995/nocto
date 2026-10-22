"""Stand-in for the third-party HTTP services nocto plugins talk to."""
import datetime
import email.utils
import hashlib
import logging
import threading
from typing import Any, Dict, List
from xml.sax.saxutils import escape, quoteattr

from flask import Flask, Response, jsonify, request

logging.getLogger("werkzeug").setLevel(logging.WARNING)

app = Flask(__name__)
lock = threading.Lock()

suggestions: Dict[str, Dict[str, Any]] = {}
suggest_requests: List[Dict[str, Any]] = []
feeds: Dict[str, Dict[str, Any]] = {}


def log_request(target: List[Dict[str, Any]]) -> None:
    with lock:
        target.append({"args": request.args.to_dict(), "headers": dict(request.headers)})


@app.route("/complete/search")
def complete_search() -> Response:
    log_request(suggest_requests)
    with lock:
        response = suggestions.get(request.args.get("q", ""), {"suggestions": []})
    if response.get("unreachable"):
        return Response(status=302, headers={"Location": "http://127.0.0.1:9/"})
    elif "status" in response:
        return Response("error", status=response["status"])
    elif "body" in response:
        return Response(response["body"], mimetype="text/xml")
    items = "".join(
        f"<CompleteSuggestion><suggestion data={quoteattr(s)}/></CompleteSuggestion>"
        for s in response["suggestions"]
    )
    return Response(f'<?xml version="1.0"?><toplevel>{items}</toplevel>', mimetype="text/xml")


@app.route("/test/suggest", methods=["POST"])
def set_suggestions() -> Response:
    body = request.get_json(force=True)
    with lock:
        suggestions[body.pop("q")] = body
    return jsonify({"ok": True})


@app.route("/test/suggest/requests")
def get_suggest_requests() -> Response:
    q = request.args.get("q")
    with lock:
        result = [r for r in suggest_requests if q is None or r["args"].get("q") == q]
    return jsonify({"requests": result})


def new_feed(name: str) -> Dict[str, Any]:
    return {"title": name, "entries": [], "status": 200, "etag": False, "last_modified": False,
            "changed": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0),
            "requests": []}


def render_feed(name: str, feed: Dict[str, Any]) -> str:
    def entry(e: Dict[str, Any]) -> str:
        author = f"<author><name>{escape(e['author'])}</name></author>" if e.get("author") else ""
        return (f"<entry><id>urn:{escape(name)}:{escape(e['title'])}</id><title>{escape(e['title'])}</title>"
                f"<link href={quoteattr(e['link'])}/><published>{e['published']}</published>"
                f"<updated>{e['published']}</updated>{author}</entry>")
    entries = "".join(entry(e) for e in reversed(feed["entries"]))
    return (f'<?xml version="1.0" encoding="utf-8"?><feed xmlns="http://www.w3.org/2005/Atom">'
            f"<id>urn:{escape(name)}</id><title>{escape(feed['title'])}</title>"
            f"<updated>{feed['changed'].isoformat()}</updated>{entries}</feed>")


@app.route("/feeds/<name>.xml")
def serve_feed(name: str) -> Response:
    with lock:
        feed = feeds.get(name)
        if feed is None:
            return Response("Not Found", status=404)
        feed["requests"].append({"headers": dict(request.headers)})
        if feed["status"] != 200:
            return Response("error", status=feed["status"])
        body = render_feed(name, feed)
        headers = {}
        if feed["etag"]:
            headers["ETag"] = '"' + hashlib.sha1(body.encode()).hexdigest() + '"'
            if request.headers.get("If-None-Match") == headers["ETag"]:
                return Response(status=304, headers=headers)
        if feed["last_modified"]:
            headers["Last-Modified"] = email.utils.format_datetime(feed["changed"], usegmt=True)
            since = request.headers.get("If-Modified-Since")
            if since and email.utils.parsedate_to_datetime(since) >= feed["changed"]:
                return Response(status=304, headers=headers)
    return Response(body, mimetype="application/atom+xml", headers=headers)


@app.route("/test/feeds/<name>", methods=["PUT"])
def configure_feed(name: str) -> Response:
    body = request.get_json(force=True)
    with lock:
        feed = feeds.setdefault(name, new_feed(name))
        feed.update({k: v for k, v in body.items() if k in ("title", "status", "etag", "last_modified")})
    return jsonify({"ok": True})


@app.route("/test/feeds/<name>/entries", methods=["POST"])
def publish_entries(name: str) -> Response:
    with lock:
        feed = feeds.setdefault(name, new_feed(name))
        for item in request.get_json(force=True):
            # Strictly increasing timestamps: the bot only announces entries newer than the last one it saw.
            now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
            feed["changed"] = max(now, feed["changed"] + datetime.timedelta(seconds=1))
            feed["entries"].append(dict(item, published=feed["changed"].isoformat()))
    return jsonify({"ok": True})


@app.route("/test/feeds/<name>/requests")
def feed_requests(name: str) -> Response:
    with lock:
        return jsonify({"requests": list(feeds.get(name, {}).get("requests", []))})


@app.route("/test/reset", methods=["POST"])
def reset() -> Response:
    with lock:
        suggestions.clear()
        suggest_requests.clear()
        feeds.clear()
    return jsonify({"ok": True})


@app.route("/test/health")
def health() -> Response:
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090, threaded=True)

"""Stand-in for the third-party HTTP services nocto plugins talk to."""
import logging
import threading
from typing import Any, Dict, List
from xml.sax.saxutils import quoteattr

from flask import Flask, Response, jsonify, request

logging.getLogger("werkzeug").setLevel(logging.WARNING)

app = Flask(__name__)
lock = threading.Lock()

suggestions: Dict[str, Dict[str, Any]] = {}
suggest_requests: List[Dict[str, Any]] = []


def log_request(target: List[Dict[str, Any]]) -> None:
    with lock:
        target.append({"args": request.args.to_dict(), "headers": dict(request.headers)})


@app.route("/complete/search")
def complete_search() -> Response:
    log_request(suggest_requests)
    with lock:
        response = suggestions.get(request.args.get("q", ""), {"suggestions": []})
    if "status" in response:
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


@app.route("/test/reset", methods=["POST"])
def reset() -> Response:
    with lock:
        suggestions.clear()
        suggest_requests.clear()
    return jsonify({"ok": True})


@app.route("/test/health")
def health() -> Response:
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090, threaded=True)

"""Fake Telegram Bot API.

The bot side is served over HTTPS (nocto always uses an https agent) with a
certificate signed by a CA written to /certs, the test side over plain HTTP.
All state is namespaced by bot token, so several bots can share one mock.
"""
import base64
import datetime
import hashlib
import ipaddress
import json
import logging
import os
import ssl
import threading
import time
from typing import Any, Dict, List, Optional

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
from flask import Flask, Response, jsonify, request
from werkzeug.serving import make_server

logging.getLogger("werkzeug").setLevel(logging.WARNING)

CERT_DIR = os.environ.get("CERT_DIR", "/certs")
HOSTNAMES = os.environ.get("CERT_HOSTNAMES", "telegram-mock,localhost").split(",")
BOT_PORT = int(os.environ.get("BOT_PORT", "8443"))
TEST_PORT = int(os.environ.get("TEST_PORT", "8081"))
MAX_POLL_HOLD = 10.0
UPDATE_KEYS = ("message", "edited_message", "inline_query", "callback_query")

app = Flask(__name__)
cond = threading.Condition()
https_ready = threading.Event()

next_update_id = 1
next_message_id = 1000
next_seq = 1
pending: Dict[str, List[Dict[str, Any]]] = {}
acked: Dict[str, int] = {}
calls: Dict[str, List[Dict[str, Any]]] = {}
files: Dict[str, Dict[str, Any]] = {}


def bot_identity(token: str) -> Dict[str, Any]:
    bot_id, _, name = token.partition(":")
    return {
        "id": int(bot_id) if bot_id.isdigit() else 1,
        "is_bot": True,
        "first_name": f"Nocto {name}",
        "username": f"nocto_{name}_bot",
    }


def ok(result: Any) -> Response:
    return jsonify({"ok": True, "result": result})


def decode_param(value: Any) -> Any:
    if isinstance(value, str) and value[:1] in ("{", "["):
        try:
            return json.loads(value)
        except ValueError:
            return value
    return value


def request_params() -> Dict[str, Any]:
    params: Dict[str, Any] = {}
    if request.is_json:
        params.update(request.get_json(silent=True) or {})
    params.update(request.form.to_dict())
    params.update(request.args.to_dict())
    return {key: decode_param(value) for key, value in params.items()}


def request_files() -> Dict[str, Dict[str, Any]]:
    result = {}
    for field, upload in request.files.items():
        content = upload.read()
        result[field] = {
            "filename": upload.filename,
            "content_type": upload.mimetype,
            "size": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
            "magic": content[:16].hex(),
        }
    return result


def record(token: str, method: str, params: Dict[str, Any], uploads: Dict[str, Any]) -> Dict[str, Any]:
    global next_message_id, next_seq
    with cond:
        entry = {
            "seq": next_seq,
            "method": method,
            "chat_id": str(params["chat_id"]) if "chat_id" in params else None,
            "params": params,
            "files": uploads,
            "message_id": next_message_id,
            "time": time.time(),
        }
        next_seq += 1
        next_message_id += 1
        calls.setdefault(token, []).append(entry)
    return entry


def get_updates(token: str, params: Dict[str, Any]) -> Response:
    offset = int(params.get("offset") or 0)
    hold = min(float(params.get("timeout") or 0), MAX_POLL_HOLD)
    deadline = time.time() + hold
    with cond:
        if offset:
            acked[token] = max(acked.get(token, 0), offset)
            pending[token] = [u for u in pending.get(token, []) if u["update_id"] >= offset]
        while not pending.get(token) and time.time() < deadline:
            cond.wait(deadline - time.time())
        return ok(list(pending.get(token, [])))


@app.route("/bot<token>/<method>", methods=["GET", "POST"])
def bot_api(token: str, method: str) -> Response:
    params = request_params()
    if method == "getMe":
        return ok(bot_identity(token))
    elif method == "getUpdates":
        return get_updates(token, params)
    elif method == "getFile":
        record(token, method, params, {})
        stored = files.get(str(params.get("file_id")))
        if not stored:
            return jsonify({"ok": False, "error_code": 400,
                            "description": "Bad Request: invalid file_id"}), 400
        return ok({"file_id": stored["file_id"], "file_size": len(stored["content"]), "file_path": stored["file_path"]})

    entry = record(token, method, params, request_files())
    if method in ("sendChatAction", "answerInlineQuery") or not method.startswith(("send", "forward")):
        return ok(True)
    return ok({
        "message_id": entry["message_id"],
        "date": int(time.time()),
        "chat": {"id": int(params.get("chat_id") or 0)},
        "text": params.get("text"),
    })


@app.route("/file/bot<token>/<path:file_path>")
def download(token: str, file_path: str) -> Response:
    for stored in files.values():
        if stored["file_path"] == file_path:
            stored["downloads"] += 1
            return Response(stored["content"], mimetype="application/octet-stream")
    return Response("Not Found", status=404)


@app.route("/test/<token>/updates", methods=["POST"])
def inject(token: str) -> Response:
    global next_update_id
    body = request.get_json(force=True)
    batch = body if isinstance(body, list) else [body]
    ids = []
    with cond:
        for item in batch:
            update = dict(item) if any(key in item for key in UPDATE_KEYS) else {"message": item}
            update["update_id"] = next_update_id
            next_update_id += 1
            pending.setdefault(token, []).append(update)
            ids.append(update["update_id"])
        cond.notify_all()
    return jsonify({"update_ids": ids})


@app.route("/test/<token>/acked")
def is_acked(token: str) -> Response:
    update_id = int(request.args["update_id"])
    with cond:
        return jsonify({"acked": acked.get(token, 0) > update_id})


@app.route("/test/<token>/calls")
def list_calls(token: str) -> Response:
    chat_id: Optional[str] = request.args.get("chat_id")
    method: Optional[str] = request.args.get("method")
    with cond:
        result = [
            c for c in calls.get(token, [])
            if (chat_id is None or c["chat_id"] == chat_id) and (method is None or c["method"] == method)
        ]
    return jsonify({"calls": result})


@app.route("/test/files", methods=["POST"])
def register_file() -> Response:
    body = request.get_json(force=True)
    file_id = body["file_id"]
    files[file_id] = {
        "file_id": file_id,
        "file_path": body.get("file_path") or f"documents/{file_id}",
        "content": base64.b64decode(body["content_b64"]),
        "downloads": 0,
    }
    return jsonify({"ok": True})


@app.route("/test/files/<file_id>")
def file_stats(file_id: str) -> Response:
    stored = files.get(file_id)
    if not stored:
        return jsonify({"ok": False}), 404
    return jsonify({"ok": True, "downloads": stored["downloads"]})


@app.route("/test/reset", methods=["POST"])
def reset() -> Response:
    with cond:
        calls.clear()
        files.clear()
        for queue in pending.values():
            queue.clear()
    return jsonify({"ok": True})


@app.route("/test/health")
def health() -> Response:
    if not https_ready.is_set():
        return jsonify({"ok": False}), 503
    return jsonify({"ok": True})


def make_certificates() -> ssl.SSLContext:
    os.makedirs(CERT_DIR, exist_ok=True)
    ca_cert_path = os.path.join(CERT_DIR, "ca.pem")
    ca_key_path = os.path.join(CERT_DIR, "ca.key")
    now = datetime.datetime.now(datetime.timezone.utc)

    # Reuse an existing CA: bots that already trust it keep working when only the mock restarts.
    if os.path.exists(ca_cert_path) and os.path.exists(ca_key_path):
        with open(ca_key_path, "rb") as fh:
            ca_key = serialization.load_pem_private_key(fh.read(), password=None)
        with open(ca_cert_path, "rb") as fh:
            ca_cert = x509.load_pem_x509_certificate(fh.read())
    else:
        ca_key = ec.generate_private_key(ec.SECP256R1())
        ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "nocto acceptance CA")])
        ca_cert = (
            x509.CertificateBuilder()
            .subject_name(ca_name).issuer_name(ca_name)
            .public_key(ca_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(days=1))
            .not_valid_after(now + datetime.timedelta(days=30))
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .add_extension(x509.KeyUsage(
                digital_signature=True, content_commitment=False, key_encipherment=False,
                data_encipherment=False, key_agreement=False, key_cert_sign=True,
                crl_sign=True, encipher_only=False, decipher_only=False), critical=True)
            .sign(ca_key, hashes.SHA256())
        )
        with open(ca_key_path + ".tmp", "wb") as fh:
            fh.write(ca_key.private_bytes(
                serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption(),
            ))
        os.replace(ca_key_path + ".tmp", ca_key_path)
        with open(ca_cert_path + ".tmp", "wb") as fh:
            fh.write(ca_cert.public_bytes(serialization.Encoding.PEM))
        os.replace(ca_cert_path + ".tmp", ca_cert_path)

    leaf_key = ec.generate_private_key(ec.SECP256R1())
    alt_names: List[x509.GeneralName] = []
    for name in HOSTNAMES:
        try:
            alt_names.append(x509.IPAddress(ipaddress.ip_address(name)))
        except ValueError:
            alt_names.append(x509.DNSName(name))
    leaf_cert = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, HOSTNAMES[0])]))
        .issuer_name(ca_cert.subject)
        .public_key(leaf_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=2))
        .add_extension(x509.SubjectAlternativeName(alt_names), critical=False)
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
        .sign(ca_key, hashes.SHA256())
    )
    leaf_path = os.path.join(CERT_DIR, "server.pem")
    key_path = os.path.join(CERT_DIR, "server.key")
    with open(leaf_path, "wb") as fh:
        fh.write(leaf_cert.public_bytes(serialization.Encoding.PEM))
        fh.write(ca_cert.public_bytes(serialization.Encoding.PEM))
    with open(key_path, "wb") as fh:
        fh.write(leaf_key.private_bytes(serialization.Encoding.PEM,
                                        serialization.PrivateFormat.PKCS8,
                                        serialization.NoEncryption()))
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(leaf_path, key_path)
    return context


def main() -> None:
    context = make_certificates()
    bot_server = make_server("0.0.0.0", BOT_PORT, app, threaded=True, ssl_context=context)
    test_server = make_server("0.0.0.0", TEST_PORT, app, threaded=True)
    threading.Thread(target=bot_server.serve_forever, daemon=True).start()
    https_ready.set()
    test_server.serve_forever()


if __name__ == "__main__":
    main()

import os
import tempfile

os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402


def test_api_flow():
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}

        r = client.post("/api/convert", json={"text": "convert 5 km to miles"})
        assert r.status_code == 200
        assert r.json()["result"] == pytest.approx(3.10686, rel=1e-4)

        bad = client.post("/api/convert", json={"text": "convert 5 kg to meters"})
        assert bad.status_code == 422
        assert "Can't convert" in bad.json()["detail"]

        assert len(client.get("/api/history").json()) == 1
        assert "length" in client.get("/api/units").json()
        assert client.delete("/api/history").json() == {"cleared": True}
        assert client.get("/api/history").json() == []

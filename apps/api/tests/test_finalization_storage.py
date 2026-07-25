import hashlib

from packages.finalization.storage import FinalArtifactStore


def test_final_artifact_store_persists_master_and_qc_report(tmp_path) -> None:
    store = FinalArtifactStore(str(tmp_path))
    master = store.persist_bytes(
        b"master-video",
        series_id="series-1",
        job_id="final-1",
        filename="episode-master.mp4",
        kind="episode_master",
        duration_seconds=42.0,
    )
    report = store.persist_bytes(
        b'{"passed": true}',
        series_id="series-1",
        job_id="final-1",
        filename="qc-report.json",
        kind="qc_report",
    )

    assert master.url == "/artifacts/series-1/final-episodes/final-1/episode-master.mp4"
    assert master.checksum_sha256 == hashlib.sha256(b"master-video").hexdigest()
    assert master.duration_seconds == 42.0
    assert report.mime_type == "application/json"
    assert report.storage_path.endswith("qc-report.json")

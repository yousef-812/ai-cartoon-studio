import hashlib

from packages.lipsync.models import RenderedLipSyncVideo
from packages.lipsync.storage import persist_lip_sync_video


def test_lip_sync_output_is_stored_with_public_url_and_checksum(tmp_path) -> None:
    content = b"final-lip-sync-video"
    video = persist_lip_sync_video(
        str(tmp_path),
        RenderedLipSyncVideo(
            content=content,
            filename="result.mp4",
            mime_type="video/mp4",
            duration_seconds=8.5,
            metadata={"segments": 2},
        ),
        series_id="series-1",
        job_id="lip-sync-1",
    )

    assert video.url == "/artifacts/series-1/lip-sync-shots/lip-sync-1/lip-sync.mp4"
    assert video.checksum_sha256 == hashlib.sha256(content).hexdigest()
    assert video.size_bytes == len(content)
    assert video.duration_seconds == 8.5
    assert open(video.storage_path, "rb").read() == content

import asyncio

import httpx

from packages.lipsync.http_provider import SelfHostedLipSyncProvider
from packages.lipsync.models import DialoguePlacementSegment, LipSyncGenerationSpec


def test_lip_sync_provider_uploads_video_audio_and_manifest(tmp_path) -> None:
    video_path = tmp_path / "shot.mp4"
    audio_path = tmp_path / "line.wav"
    video_path.write_bytes(b"source-video")
    audio_path.write_bytes(b"source-audio")
    observed: dict[str, bytes] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/lip-sync"
        body = request.read()
        observed["body"] = body
        assert b'"character_name": "Mira"' in body
        assert b'"audio_field": "audio_0"' in body
        assert b"shot.mp4" in body
        assert b"line.wav" in body
        return httpx.Response(
            200,
            content=b"lip-synced-video",
            headers={"content-type": "video/mp4"},
        )

    provider = SelfHostedLipSyncProvider(
        base_url="https://lip.example",
        api_key="secret",
        transport=httpx.MockTransport(handler),
    )
    rendered = asyncio.run(
        provider.synthesize(
            LipSyncGenerationSpec(
                input_video_path=str(video_path),
                scene_number=1,
                shot_number=2,
                duration_seconds=4,
                segments=[
                    DialoguePlacementSegment(
                        voice_job_id="voice-1",
                        dialogue_order=1,
                        character_id="character-1",
                        character_name="Mira",
                        audio_path=str(audio_path),
                        start_time_seconds=0.25,
                        end_time_seconds=2.25,
                        text="The engine is stable now.",
                    )
                ],
            )
        )
    )

    assert observed["body"]
    assert rendered.content == b"lip-synced-video"
    assert rendered.mime_type == "video/mp4"
    assert rendered.duration_seconds == 4

import shutil
import subprocess
import tempfile
from pathlib import Path

from packages.sound.errors import SoundMixError, SoundMixUnavailableError
from packages.sound.models import (
    GeneratedSoundAsset,
    RenderedSoundMix,
    SoundCueKind,
    SoundMixGenerationSpec,
)


class FFmpegSoundMixer:
    def __init__(self, binary: str = "ffmpeg") -> None:
        self.binary = binary

    def available(self) -> bool:
        return shutil.which(self.binary) is not None

    def build_command(
        self,
        spec: SoundMixGenerationSpec,
        assets: list[GeneratedSoundAsset],
        output_path: str,
    ) -> list[str]:
        if len(assets) != len(spec.cues):
            raise SoundMixError("Every planned sound cue must have one generated asset")
        command = [self.binary, "-y", "-i", spec.input_video_path]
        for cue, asset in zip(spec.cues, assets, strict=True):
            if cue.loop:
                command.extend(["-stream_loop", "-1"])
            command.extend(["-i", asset.storage_path])

        filters: list[str] = []
        mix_labels: list[str] = []
        if spec.source_has_dialogue:
            filters.append("[0:a]aresample=48000,asetpts=PTS-STARTPTS[dialogue]")
            mix_labels.append("[dialogue]")

        duck_expression = self._duck_expression(spec)
        for index, (cue, asset) in enumerate(zip(spec.cues, assets, strict=True), start=1):
            if not Path(asset.storage_path).is_file():
                raise SoundMixError(f"Generated sound asset is missing: {asset.storage_path}")
            chain = [
                "aresample=48000",
                f"atrim=duration={cue.duration_seconds:.3f}",
                "asetpts=PTS-STARTPTS",
            ]
            if cue.fade_in_seconds > 0:
                chain.append(f"afade=t=in:st=0:d={cue.fade_in_seconds:.3f}")
            if cue.fade_out_seconds > 0:
                fade_start = max(0.0, cue.duration_seconds - cue.fade_out_seconds)
                chain.append(
                    f"afade=t=out:st={fade_start:.3f}:d={cue.fade_out_seconds:.3f}"
                )
            chain.append(f"volume={cue.gain_db:.2f}dB")
            if cue.kind == SoundCueKind.MUSIC and duck_expression:
                chain.append(
                    f"volume={spec.dialogue_ducking_db:.2f}dB:enable='{duck_expression}'"
                )
            delay_ms = round(cue.start_time_seconds * 1000)
            if delay_ms:
                chain.append(f"adelay={delay_ms}:all=1")
            label = f"cue{index}"
            filters.append(f"[{index}:a]{','.join(chain)}[{label}]")
            mix_labels.append(f"[{label}]")

        if not mix_labels:
            raise SoundMixError("Sound mix has no audio inputs")
        filters.append(
            f"{''.join(mix_labels)}amix=inputs={len(mix_labels)}:duration=longest:"
            "dropout_transition=0,"
            f"atrim=duration={spec.duration_seconds:.3f},"
            f"loudnorm=I={spec.target_loudness_lufs:.2f}:TP=-1.5:LRA=11[mix]"
        )
        command.extend(
            [
                "-filter_complex",
                ";".join(filters),
                "-map",
                "0:v:0",
                "-map",
                "[mix]",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-t",
                f"{spec.duration_seconds:.3f}",
                "-movflags",
                "+faststart",
                output_path,
            ]
        )
        return command

    def mix(
        self,
        spec: SoundMixGenerationSpec,
        assets: list[GeneratedSoundAsset],
    ) -> RenderedSoundMix:
        if not self.available():
            raise SoundMixUnavailableError("FFmpeg is not installed or not available on PATH")
        suffix = {"mov": ".mov", "mkv": ".mkv"}.get(spec.output_format, ".mp4")
        with tempfile.TemporaryDirectory(prefix="cartoon-sound-") as directory:
            output_path = Path(directory) / f"sound-mix{suffix}"
            command = self.build_command(spec, assets, str(output_path))
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=max(120, int(spec.duration_seconds * 20)),
            )
            if completed.returncode != 0:
                detail = completed.stderr[-6000:] if completed.stderr else "Unknown FFmpeg error"
                raise SoundMixError(f"FFmpeg sound mix failed: {detail}")
            content = output_path.read_bytes()
            if not content:
                raise SoundMixError("FFmpeg produced an empty sound mix")
        mime_type = {
            ".mov": "video/quicktime",
            ".mkv": "video/x-matroska",
        }.get(suffix, "video/mp4")
        return RenderedSoundMix(
            content=content,
            filename=f"scene-{spec.scene_number}-shot-{spec.shot_number}-sound-mix{suffix}",
            mime_type=mime_type,
            duration_seconds=spec.duration_seconds,
            metadata={
                "scene_number": spec.scene_number,
                "shot_number": spec.shot_number,
                "cue_count": len(spec.cues),
                "target_loudness_lufs": spec.target_loudness_lufs,
                **spec.metadata,
            },
        )

    @staticmethod
    def _duck_expression(spec: SoundMixGenerationSpec) -> str:
        return "+".join(
            f"between(t,{window.start_time_seconds:.3f},{window.end_time_seconds:.3f})"
            for window in spec.dialogue_windows
        )

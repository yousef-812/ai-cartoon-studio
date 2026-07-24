import asyncio
from pathlib import Path


class FFmpegRenderEngine:
    async def probe(self) -> bool:
        process = await asyncio.create_subprocess_exec(
            "ffmpeg", "-version", stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )
        return await process.wait() == 0

    async def render_episode(self, manifest_path: Path, output_path: Path) -> Path:
        raise NotImplementedError("Implement manifest-driven final rendering.")

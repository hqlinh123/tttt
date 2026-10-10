import asyncio

import base64

import logging

import mimetypes

import os

import shutil

import subprocess

import uuid

from datetime import datetime

from pathlib import Path

from urllib.parse import unquote, urlparse



import httpx

from fastapi import HTTPException, UploadFile

from runwayml import RunwayML, TaskFailedError



from app.infrastructure.repositories.video_repository import VideoRepository



logger = logging.getLogger(__name__)





class VideoService:

    """

    One-file media service.



    Capabilities:

      - Text -> Voice: remains in VoiceService / Viterbox (NOT Runway here)

      - Text -> Video: Runway

      - Image(s) -> Video: Runway

      - Video -> Video: Runway

      - Text -> Image: Runway

      - Image(s) + Text -> Image: Runway

      - Runway video + Viterbox voice -> final MP4: FFmpeg



    The old generate_video() entry point is retained for backward compatibility.

    """




    def __init__(

        self,

        video_repo: VideoRepository,

    ):

        self.video_repo = video_repo



        self.output_dir = Path("outputs")

        self.video_dir = self.output_dir / "videos"

        self.image_dir = self.output_dir / "video-images"

        self.generated_image_dir = self.output_dir / "generated-images"

        self.ai_video_dir = self.output_dir / "ai-videos"

        self.uploaded_video_dir = self.output_dir / "uploaded-videos"



        for directory in (

            self.output_dir,

            self.video_dir,

            self.image_dir,

            self.generated_image_dir,

            self.ai_video_dir,

            self.uploaded_video_dir,

        ):

            directory.mkdir(

                parents=True,

                exist_ok=True,

            )



        self.runway_api_key = os.getenv(

            "RUNWAYML_API_SECRET",

            "",

        )



        self.runway_video_model = os.getenv(

            "RUNWAY_VIDEO_MODEL",

            "gen4.5",

        )



        self.runway_reference_video_model = os.getenv(

            "RUNWAY_REFERENCE_VIDEO_MODEL",

            "seedance2_5",

        )



        self.runway_image_model = os.getenv(

            "RUNWAY_IMAGE_MODEL",

            "gen4_image",

        )



        self.runway = (

            RunwayML(

                api_key=self.runway_api_key

            )

            if self.runway_api_key

            else None

        )



        logger.info(

            "[RUNWAY] configured=%s "

            "video_model=%s "

            "reference_video_model=%s "

            "image_model=%s",

            bool(self.runway_api_key),

            self.runway_video_model,

            self.runway_reference_video_model,

            self.runway_image_model,

        )

    # ============================================================

    # COMMON VALIDATION

    # ============================================================



    def _require_runway(self) -> RunwayML:

        if not self.runway:

            raise HTTPException(

                status_code=500,

                detail="RUNWAYML_API_SECRET is not configured",

            )

        return self.runway



    def _build_prompt(self, prompt: str, style: str = "") -> str:

        prompt_text = (prompt or "").strip()

        if not prompt_text:

            prompt_text = (

                "Natural cinematic motion, realistic lighting, "

                "smooth camera movement and consistent subject identity."

            )



        if style and style.strip():

            prompt_text = f"{prompt_text}. Visual style: {style.strip()}."



        return prompt_text



    def _validate_duration(self, duration: int, minimum: int = 2, maximum: int = 10) -> int:

        try:

            value = int(duration)

        except (TypeError, ValueError) as exc:

            raise HTTPException(status_code=400, detail="duration must be an integer") from exc



        if value < minimum or value > maximum:

            raise HTTPException(

                status_code=400,

                detail=f"duration must be between {minimum} and {maximum} seconds",

            )

        return value



    # ============================================================

    # VOICE - VITERBOX OUTPUT RESOLUTION ONLY

    # ============================================================



    def _resolve_voice_file(self, voice_url: str) -> Path:

        """

        Examples:

          /viterbox/outputs/abc.wav

          /api/viterbox/outputs/abc.wav

          http://localhost:8000/api/viterbox/outputs/abc.wav



        -> outputs/abc.wav

        """

        if not voice_url:

            raise HTTPException(status_code=400, detail="voice_url is required")



        parsed = urlparse(voice_url)

        path = unquote(parsed.path or voice_url)

        filename = Path(path).name



        if not filename:

            raise HTTPException(status_code=400, detail="Invalid voice_url")



        voice_file = self.output_dir / filename



        if not voice_file.exists():

            raise HTTPException(

                status_code=404,

                detail=f"Generated voice not found: {filename}",

            )



        return voice_file



    # ============================================================

    # FILE SAVE

    # ============================================================



    async def _save_image(self, image: UploadFile) -> Path:

        extension = Path(image.filename or "").suffix.lower()

        allowed = {".jpg", ".jpeg", ".png", ".webp"}



        if extension not in allowed:

            raise HTTPException(

                status_code=400,

                detail="Image must be JPG, JPEG, PNG or WEBP",

            )



        destination = self.image_dir / f"{uuid.uuid4().hex}{extension}"



        try:

            await image.seek(0)

            with destination.open("wb") as buffer:

                shutil.copyfileobj(image.file, buffer)

            await image.seek(0)

            return destination

        except Exception as exc:

            logger.exception("Cannot save image")

            raise HTTPException(status_code=500, detail="Unable to save image") from exc



    async def _save_images(self, images: list[UploadFile]) -> list[Path]:

        if not images:

            raise HTTPException(status_code=400, detail="At least one image is required")



        # Seedance 2.5 currently accepts up to 30 image references.

        if len(images) > 30:

            raise HTTPException(

                status_code=400,

                detail="Maximum 30 reference images are supported",

            )



        paths: list[Path] = []

        for image in images:

            paths.append(await self._save_image(image))

        return paths



    async def _save_video(self, video: UploadFile) -> Path:

        extension = Path(video.filename or "").suffix.lower()

        allowed = {".mp4", ".mov", ".webm", ".mkv"}



        if extension not in allowed:

            raise HTTPException(

                status_code=400,

                detail="Video must be MP4, MOV, WEBM or MKV",

            )



        destination = self.uploaded_video_dir / f"{uuid.uuid4().hex}{extension}"



        try:

            await video.seek(0)

            with destination.open("wb") as buffer:

                shutil.copyfileobj(video.file, buffer)

            await video.seek(0)

            return destination

        except Exception as exc:

            logger.exception("Cannot save video")

            raise HTTPException(status_code=500, detail="Unable to save video") from exc



    # ============================================================

    # DATA URI

    # ============================================================



    def _file_to_data_uri(

        self,

        file_path: Path,

        *,

        allowed_mime_types: set[str],

        max_size_mb: int = 5,

    ) -> str:

        if not file_path.exists():

            raise HTTPException(status_code=404, detail=f"File not found: {file_path.name}")



        max_size = max_size_mb * 1024 * 1024

        if file_path.stat().st_size > max_size:

            raise HTTPException(

                status_code=400,

                detail=(

                    f"{file_path.name} is too large for a Runway Data URI. "

                    f"Maximum size is {max_size_mb} MB."

                ),

            )



        mime_type, _ = mimetypes.guess_type(str(file_path))

        if mime_type not in allowed_mime_types:

            raise HTTPException(

                status_code=400,

                detail=f"Unsupported media type: {mime_type or 'unknown'}",

            )



        with file_path.open("rb") as file:

            encoded = base64.b64encode(file.read()).decode("utf-8")



        return f"data:{mime_type};base64,{encoded}"



    def _image_to_data_uri(self, image_path: Path) -> str:

        return self._file_to_data_uri(

            image_path,

            allowed_mime_types={"image/jpeg", "image/png", "image/webp"},

            max_size_mb=5,

        )



    def _video_to_data_uri(self, video_path: Path) -> str:

        return self._file_to_data_uri(

            video_path,

            allowed_mime_types={

                "video/mp4",

                "video/quicktime",

                "video/webm",

                "video/x-matroska",

            },

            max_size_mb=5,

        )



    # ============================================================

    # RATIO

    # ============================================================



    def _get_video_size(self, aspect_ratio: str) -> tuple[int, int]:

        sizes = {

            "9:16": (1080, 1920),

            "16:9": (1920, 1080),

            "1:1": (1080, 1080),

        }

        return sizes.get(aspect_ratio, (1080, 1920))



    def _get_runway_video_ratio(self, aspect_ratio: str) -> str:

        ratios = {

            "16:9": "1280:720",

            "9:16": "720:1280",

            "1:1": "960:960",

        }

        return ratios.get(aspect_ratio, "720:1280")



    def _get_runway_image_ratio(self, aspect_ratio: str) -> str:

        ratios = {

            "16:9": "1920:1080",

            "9:16": "1080:1920",

            "1:1": "1024:1024",

        }

        return ratios.get(aspect_ratio, "1024:1024")



    # ============================================================

    # FFPROBE

    # ============================================================



    def _get_media_duration(self, media_path: Path) -> float:

        try:

            command = [

                "ffprobe",

                "-v",

                "error",

                "-show_entries",

                "format=duration",

                "-of",

                "default=noprint_wrappers=1:nokey=1",

                str(media_path),

            ]

            result = subprocess.run(

                command,

                capture_output=True,

                text=True,

                check=True,

            )

            return round(float(result.stdout.strip()), 2)

        except Exception as exc:

            logger.warning("Cannot read media duration for %s: %s", media_path, exc)

            return 0



    def _get_audio_duration(self, audio_path: Path) -> float:

        return self._get_media_duration(audio_path)



    def _get_video_duration(self, video_path: Path) -> float:

        return self._get_media_duration(video_path)



    # ============================================================

    # DOWNLOAD RUNWAY OUTPUT

    # ============================================================



    async def _download_file(self, url: str, output_path: Path) -> None:

        try:

            async with httpx.AsyncClient(timeout=180.0, follow_redirects=True) as client:

                async with client.stream("GET", url) as response:

                    response.raise_for_status()

                    with output_path.open("wb") as file:

                        async for chunk in response.aiter_bytes():

                            file.write(chunk)

        except Exception as exc:

            logger.exception("Cannot download Runway output")

            raise HTTPException(

                status_code=500,

                detail="Unable to download generated Runway output",

            ) from exc



    async def _save_runway_task_output(

        self,

        task,

        *,

        output_dir: Path,

        extension: str,

    ) -> Path:

        output = getattr(task, "output", None)

        if not output:

            raise HTTPException(

                status_code=500,

                detail="Runway completed but returned no output",

            )



        output_url = output[0]

        output_path = output_dir / f"{uuid.uuid4().hex}{extension}"

        await self._download_file(output_url, output_path)



        if not output_path.exists() or output_path.stat().st_size == 0:

            raise HTTPException(status_code=500, detail="Runway output was not downloaded")



        return output_path



    async def _run_runway_task(
            self,
            factory,
            *,
            output_dir: Path,
            extension: str,
    ) -> Path:
        try:
            logger.info("[RUNWAY] creating task...")

            task_request = await asyncio.to_thread(factory)

            task_id = getattr(task_request, "id", None)

            logger.info(
                "[RUNWAY] task created id=%s",
                task_id or "unknown",
            )

            try:
                task = await asyncio.to_thread(
                    task_request.wait_for_task_output
                )
            except TaskFailedError as exc:
                logger.error(
                    "[RUNWAY] task failed id=%s",
                    task_id or "unknown",
                )

                # Dump everything available from SDK exception.
                logger.error(
                    "[RUNWAY] exception type=%s",
                    type(exc).__name__,
                )
                logger.error(
                    "[RUNWAY] exception=%s",
                    str(exc),
                )
                logger.error(
                    "[RUNWAY] exception dict=%r",
                    getattr(exc, "__dict__", {}),
                )
                logger.error(
                    "[RUNWAY] args=%r",
                    getattr(exc, "args", None),
                )

                # Try retrieving final task directly from Runway
                # so we can see failure / failureCode.
                task_details = None

                if task_id:
                    try:
                        client = self._require_runway()

                        task_details = await asyncio.to_thread(
                            lambda: client.tasks.retrieve(task_id)
                        )

                        logger.error(
                            "[RUNWAY] failed task details=%r",
                            task_details,
                        )

                        logger.error(
                            "[RUNWAY] status=%r failure=%r failure_code=%r",
                            getattr(task_details, "status", None),
                            getattr(task_details, "failure", None),
                            getattr(task_details, "failure_code", None),
                        )

                    except Exception:
                        logger.exception(
                            "[RUNWAY] unable to retrieve failed task %s",
                            task_id,
                        )

                failure = (
                    getattr(task_details, "failure", None)
                    if task_details
                    else None
                )

                failure_code = (
                    getattr(task_details, "failure_code", None)
                    if task_details
                    else None
                )

                detail = "Runway task failed"

                if task_id:
                    detail += f" [task_id={task_id}]"

                if failure_code:
                    detail += f" [{failure_code}]"

                if failure:
                    detail += f": {failure}"
                else:
                    detail += f": {str(exc)}"

                raise HTTPException(
                    status_code=502,
                    detail=detail,
                ) from exc

            logger.info(
                "[RUNWAY] task completed id=%s status=%s",
                getattr(task, "id", task_id or "unknown"),
                getattr(task, "status", "unknown"),
            )

            logger.debug(
                "[RUNWAY] completed task=%r",
                task,
            )

            return await self._save_runway_task_output(
                task,
                output_dir=output_dir,
                extension=extension,
            )

        except HTTPException:
            raise

        except Exception as exc:
            logger.exception(
                "[RUNWAY] unexpected generation error"
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    f"Runway generation failed: "
                    f"{type(exc).__name__}: {exc}"
                ),
            ) from exc

    # ============================================================

    # 1. TEXT -> VIDEO (RUNWAY)

    # ============================================================



    async def _generate_runway_text_to_video(
        self,
        *,
        prompt: str,
        style: str,
        aspect_ratio: str,
        duration: int,
    ) -> Path:
        client = self._require_runway()

        prompt_text = self._build_prompt(
            prompt,
            style,
        )

        runway_ratio = self._get_runway_video_ratio(
            aspect_ratio
        )

        duration = self._validate_runway_video_duration(
            duration,
        )

        logger.info(
            "[RUNWAY][TEXT->VIDEO] "
            "model=%s ratio=%s duration=%s",
            self.runway_video_model,
            runway_ratio,
            duration,
        )

        return await self._run_runway_task(
            lambda: client.text_to_video.create(
                model=self.runway_video_model,
                prompt_text=prompt_text,
                ratio=runway_ratio,
                duration=duration,
            ),
            output_dir=self.ai_video_dir,
            extension=".mp4",
        )

    def _validate_runway_video_duration(self, duration: int = 4) -> int:
        try:
            value = int(duration)
        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=400,
                detail="duration must be an integer",
            ) from exc

        allowed = (4, 6, 8)

        if value not in allowed:
            raise HTTPException(
                status_code=400,
                detail="Runway video duration must be one of: 4, 6, 8 seconds",
            )

        return value
    async def generate_text_to_video(
        self, *, user_id: uuid.UUID, prompt: str, style: str = "", aspect_ratio: str = "9:16", duration: int = 5,
    ) -> dict:
        record = await self.video_repo.create_generation(user_id=user_id, generation_type="text_to_video", media_type="video", provider="runway", status="pending", prompt=prompt, style=style, aspect_ratio=aspect_ratio)
        try:
            await self.video_repo.mark_processing(record.id)
            video_path = await self._generate_runway_text_to_video(prompt=prompt, style=style, aspect_ratio=aspect_ratio, duration=duration)
            response = self._video_response(video_path, generation_type="text_to_video", prompt=prompt, style=style, aspect_ratio=aspect_ratio)
            await self.video_repo.mark_done(record.id, output_url=response["video_url"], output_filename=response["filename"], duration=response.get("duration"), extra_data={"size": response.get("size", 0)})
            response.update(record_id=record.id, status="completed", provider="runway", media_type="video")
            return response
        except Exception as exc:
            await self.video_repo.mark_failed(record.id, str(exc))
            raise

    # ============================================================
    # 2. IMAGE(S) -> VIDEO (RUNWAY)
    # ============================================================

    async def _generate_runway_image_to_video(

        self,

        *,

        image_paths: list[Path],

        prompt: str,

        style: str,

        aspect_ratio: str,

        duration: int,

    ) -> Path:

        client = self._require_runway()

        if not image_paths:

            raise HTTPException(status_code=400, detail="At least one image is required")



        prompt_text = self._build_prompt(prompt, style)

        runway_ratio = self._get_runway_video_ratio(aspect_ratio)

        duration = self._validate_runway_video_duration(duration)

        image_uris = [self._image_to_data_uri(path) for path in image_paths]



        logger.info(

            "[RUNWAY][IMAGE->VIDEO] images=%s ratio=%s duration=%s",

            len(image_uris),

            runway_ratio,

            duration,

        )



        if len(image_uris) == 1:

            # Standard image-to-video.

            return await self._run_runway_task(

                lambda: client.image_to_video.create(

                    model=self.runway_video_model,

                    prompt_image=image_uris[0],

                    prompt_text=prompt_text,

                    ratio=runway_ratio,

                    duration=duration,

                ),

                output_dir=self.ai_video_dir,

                extension=".mp4",

            )



        if len(image_uris) == 2:

            # First/last keyframes supported by Runway image_to_video.

            prompt_images = [

                {"uri": image_uris[0], "position": "first"},

                {"uri": image_uris[1], "position": "last"},

            ]

            return await self._run_runway_task(

                lambda: client.image_to_video.create(

                    model=self.runway_video_model,

                    prompt_image=prompt_images,

                    prompt_text=prompt_text,

                    ratio=runway_ratio,

                    duration=duration,

                ),

                output_dir=self.ai_video_dir,

                extension=".mp4",

            )



        # 3..30 images: use Seedance 2.5 references.

        # Images are referenced in the prompt as [Image 1], [Image 2], ...

        references = [{"uri": uri} for uri in image_uris]

        multi_prompt = (

            f"{prompt_text} Use the supplied reference images consistently. "

            "Preserve character identity, clothing, colors and visual continuity "

            "across the generated shot."

        )



        return await self._run_runway_task(

            lambda: client.text_to_video.create(

                model=self.runway_reference_video_model,

                prompt_text=multi_prompt,

                ratio=runway_ratio,

                duration=duration,

                references=references,

                audio=False,

            ),

            output_dir=self.ai_video_dir,

            extension=".mp4",

        )



    async def generate_image_to_video(
        self, *, user_id: uuid.UUID, images: list[UploadFile], prompt: str, style: str = "", aspect_ratio: str = "9:16", duration: int = 5,
    ) -> dict:
        image_paths = await self._save_images(images)
        image_urls = [f"/video-images/{path.name}" for path in image_paths]
        record = await self.video_repo.create_generation(user_id=user_id, generation_type="image_to_video", media_type="video", provider="runway", status="pending", prompt=prompt, style=style, aspect_ratio=aspect_ratio, source_image_url=image_urls[0] if image_urls else None, source_image_urls=image_urls)
        try:
            await self.video_repo.mark_processing(record.id)
            video_path = await self._generate_runway_image_to_video(image_paths=image_paths, prompt=prompt, style=style, aspect_ratio=aspect_ratio, duration=duration)
            response = self._video_response(video_path, generation_type="image_to_video", prompt=prompt, style=style, aspect_ratio=aspect_ratio)
            response["image_urls"] = image_urls
            response["image_count"] = len(image_paths)
            await self.video_repo.mark_done(record.id, output_url=response["video_url"], output_filename=response["filename"], duration=response.get("duration"), source_image_url=image_urls[0] if image_urls else None, source_image_urls=image_urls, extra_data={"size": response.get("size", 0), "image_count": len(image_paths)})
            response.update(record_id=record.id, status="completed", provider="runway", media_type="video")
            return response
        except Exception as exc:
            await self.video_repo.mark_failed(record.id, str(exc))
            raise

    # ============================================================
    # 3. VIDEO -> VIDEO (RUNWAY)
    # ============================================================

    async def _generate_runway_video_to_video(

        self,

        *,

        video_path: Path,

        prompt: str,

        style: str,

        aspect_ratio: str,

        duration: int | str = "auto",

        mode: str = "reference",

        reference_image_paths: list[Path] | None = None,

    ) -> Path:

        client = self._require_runway()

        prompt_text = self._build_prompt(prompt, style)

        video_uri = self._video_to_data_uri(video_path)

        runway_ratio = self._get_runway_video_ratio(aspect_ratio)



        if mode not in {"reference", "extend", "edit"}:

            raise HTTPException(

                status_code=400,

                detail="mode must be reference, extend or edit",

            )



        references = [

            {"uri": self._image_to_data_uri(path)}

            for path in (reference_image_paths or [])

        ]



        kwargs = {

            "model": self.runway_reference_video_model,

            "prompt_video": video_uri,

            "prompt_text": prompt_text,

            "mode": mode,

            "audio": False,

        }



        if references:

            kwargs["references"] = references



        if mode == "edit":

            kwargs["duration"] = "auto"

        else:

            kwargs["duration"] = duration



        if mode != "extend" and mode != "edit":

            kwargs["ratio"] = runway_ratio



        logger.info(

            "[RUNWAY][VIDEO->VIDEO] model=%s mode=%s refs=%s",

            self.runway_reference_video_model,

            mode,

            len(references),

        )



        return await self._run_runway_task(

            lambda: client.video_to_video.create(**kwargs),

            output_dir=self.ai_video_dir,

            extension=".mp4",

        )



    async def generate_video_to_video(
        self, *, user_id: uuid.UUID, video: UploadFile, prompt: str, style: str = "", aspect_ratio: str = "9:16", duration: int | str = "auto", mode: str = "reference", reference_images: list[UploadFile] | None = None,
    ) -> dict:
        video_path = await self._save_video(video)
        reference_paths = await self._save_images(reference_images) if reference_images else []
        source_video_url = f"/uploaded-videos/{video_path.name}"
        reference_urls = [f"/video-images/{path.name}" for path in reference_paths]
        generation_type = "video_reference_to_video" if reference_paths else "video_to_video"
        record = await self.video_repo.create_generation(user_id=user_id, generation_type=generation_type, media_type="video", provider="runway", status="pending", prompt=prompt, style=style, aspect_ratio=aspect_ratio, source_video_url=source_video_url, reference_image_urls=reference_urls, extra_data={"mode": mode})
        try:
            await self.video_repo.mark_processing(record.id)
            output_path = await self._generate_runway_video_to_video(video_path=video_path, prompt=prompt, style=style, aspect_ratio=aspect_ratio, duration=duration, mode=mode, reference_image_paths=reference_paths)
            response = self._video_response(output_path, generation_type=generation_type, prompt=prompt, style=style, aspect_ratio=aspect_ratio)
            response["source_video_url"] = source_video_url
            response["reference_image_urls"] = reference_urls
            response["reference_image_count"] = len(reference_urls)
            await self.video_repo.mark_done(record.id, output_url=response["video_url"], output_filename=response["filename"], duration=response.get("duration"), source_video_url=source_video_url, reference_image_urls=reference_urls, extra_data={"size": response.get("size", 0), "mode": mode, "reference_image_count": len(reference_urls)})
            response.update(record_id=record.id, status="completed", provider="runway", media_type="video")
            return response
        except Exception as exc:
            await self.video_repo.mark_failed(record.id, str(exc))
            raise

    # ============================================================
    # 4. TEXT -> IMAGE (RUNWAY)
    # ============================================================

    async def _generate_runway_text_to_image(

        self,

        *,

        prompt: str,

        style: str,

        aspect_ratio: str,

        reference_image_paths: list[Path] | None = None,

    ) -> Path:

        client = self._require_runway()

        prompt_text = self._build_prompt(prompt, style)

        runway_ratio = self._get_runway_image_ratio(aspect_ratio)



        references = []

        for index, path in enumerate(reference_image_paths or [], start=1):

            references.append(

                {

                    "uri": self._image_to_data_uri(path),

                    "tag": f"Reference{index}",

                }

            )



        kwargs = {

            "model": self.runway_image_model,

            "ratio": runway_ratio,

            "prompt_text": prompt_text,

        }

        if references:

            kwargs["reference_images"] = references



        logger.info(

            "[RUNWAY][TEXT/IMAGE->IMAGE] model=%s refs=%s ratio=%s",

            self.runway_image_model,

            len(references),

            runway_ratio,

        )



        return await self._run_runway_task(

            lambda: client.text_to_image.create(**kwargs),

            output_dir=self.generated_image_dir,

            extension=".png",

        )



    async def generate_text_to_image(
        self, *, user_id: uuid.UUID, prompt: str, style: str = "", aspect_ratio: str = "1:1",
    ) -> dict:
        record = await self.video_repo.create_generation(user_id=user_id, generation_type="text_to_image", media_type="image", provider="runway", status="pending", prompt=prompt, style=style, aspect_ratio=aspect_ratio)
        try:
            await self.video_repo.mark_processing(record.id)
            image_path = await self._generate_runway_text_to_image(prompt=prompt, style=style, aspect_ratio=aspect_ratio)
            response = self._image_response(image_path, generation_type="text_to_image", prompt=prompt, style=style, aspect_ratio=aspect_ratio)
            await self.video_repo.mark_done(record.id, output_url=response["image_url"], output_filename=response["filename"], extra_data={"size": response.get("size", 0)})
            response.update(record_id=record.id, status="completed", provider="runway", media_type="image")
            return response
        except Exception as exc:
            await self.video_repo.mark_failed(record.id, str(exc))
            raise

    # ============================================================
    # 5. IMAGE(S) + TEXT -> IMAGE (RUNWAY)
    # ============================================================

    async def generate_image_to_image(
        self, *, user_id: uuid.UUID, images: list[UploadFile], prompt: str, style: str = "", aspect_ratio: str = "1:1",
    ) -> dict:
        image_paths = await self._save_images(images)
        reference_urls = [f"/video-images/{path.name}" for path in image_paths]
        record = await self.video_repo.create_generation(user_id=user_id, generation_type="image_to_image", media_type="image", provider="runway", status="pending", prompt=prompt, style=style, aspect_ratio=aspect_ratio, source_image_url=reference_urls[0] if reference_urls else None, source_image_urls=reference_urls, reference_image_urls=reference_urls)
        try:
            await self.video_repo.mark_processing(record.id)
            output_path = await self._generate_runway_text_to_image(prompt=prompt, style=style, aspect_ratio=aspect_ratio, reference_image_paths=image_paths)
            response = self._image_response(output_path, generation_type="image_to_image", prompt=prompt, style=style, aspect_ratio=aspect_ratio)
            response["reference_image_urls"] = reference_urls
            response["reference_image_count"] = len(reference_urls)
            await self.video_repo.mark_done(record.id, output_url=response["image_url"], output_filename=response["filename"], source_image_url=reference_urls[0] if reference_urls else None, source_image_urls=reference_urls, reference_image_urls=reference_urls, extra_data={"size": response.get("size", 0), "reference_image_count": len(reference_urls)})
            response.update(record_id=record.id, status="completed", provider="runway", media_type="image")
            return response
        except Exception as exc:
            await self.video_repo.mark_failed(record.id, str(exc))
            raise

    # ============================================================
    # FFMPEG - RUNWAY VIDEO + VITERBOX VOICE
    # ============================================================

    async def _merge_video_and_voice(

        self,

        *,

        video_path: Path,

        voice_path: Path,

        output_path: Path,

        aspect_ratio: str,

    ) -> None:

        width, height = self._get_video_size(aspect_ratio)



        video_filter = (

            f"scale={width}:{height}:force_original_aspect_ratio=increase,"

            f"crop={width}:{height},fps=30,format=yuv420p"

        )



        command = [

            "ffmpeg",

            "-y",

            "-i",

            str(video_path),

            "-i",

            str(voice_path),

            "-map",

            "0:v:0",

            "-map",

            "1:a:0",

            "-vf",

            video_filter,

            "-c:v",

            "libx264",

            "-preset",

            "medium",

            "-crf",

            "20",

            "-pix_fmt",

            "yuv420p",

            "-c:a",

            "aac",

            "-b:a",

            "192k",

            "-shortest",

            "-movflags",

            "+faststart",

            str(output_path),

        ]



        logger.info("[FFMPEG] command: %s", " ".join(command))



        try:

            process = await asyncio.create_subprocess_exec(

                *command,

                stdout=asyncio.subprocess.PIPE,

                stderr=asyncio.subprocess.PIPE,

            )

            _, stderr = await process.communicate()

        except FileNotFoundError as exc:

            raise HTTPException(

                status_code=500,

                detail="FFmpeg is not installed on the server",

            ) from exc



        if process.returncode != 0:

            error_message = stderr.decode("utf-8", errors="ignore")

            logger.error("[FFMPEG] failed:\n%s", error_message)

            raise HTTPException(

                status_code=500,

                detail="FFmpeg failed to merge Runway video and Viterbox voice",

            )



        if not output_path.exists() or output_path.stat().st_size == 0:

            raise HTTPException(status_code=500, detail="Final video output was not created")



    async def compose_video_with_voice(

        self,

        *,

        video_path: Path,

        voice_url: str,

        aspect_ratio: str = "9:16",

    ) -> dict:

        voice_path = self._resolve_voice_file(voice_url)

        video_id = uuid.uuid4().hex

        output_path = self.video_dir / f"{video_id}.mp4"



        await self._merge_video_and_voice(

            video_path=video_path,

            voice_path=voice_path,

            output_path=output_path,

            aspect_ratio=aspect_ratio,

        )



        response = self._video_response(

            output_path,

            generation_type="video_with_viterbox_voice",

            prompt="",

            style="",

            aspect_ratio=aspect_ratio,

        )

        response["voice_url"] = voice_url

        return response



    # ============================================================

    # BACKWARD COMPATIBILITY: OLD GENERATE VIDEO FLOW

    # ============================================================



    async def generate_video(
        self,
        *,
        user_id: uuid.UUID,
        voice_url: str,
        prompt: str,
        style: str,
        aspect_ratio: str,
        image: UploadFile | None = None,
        images: list[UploadFile] | None = None,
        duration: int = 5,
    ) -> dict:
        """Backward-compatible image(s) -> Runway video -> Viterbox voice -> FFmpeg flow."""
        voice_path = self._resolve_voice_file(voice_url)
        voice_duration = self._get_audio_duration(voice_path)
        if voice_duration <= 0:
            raise HTTPException(status_code=400, detail="Unable to determine voice duration")

        upload_images: list[UploadFile] = []
        if images:
            upload_images.extend(images)
        elif image is not None:
            upload_images.append(image)
        if not upload_images:
            raise HTTPException(status_code=400, detail="image or images is required")

        image_paths = await self._save_images(upload_images)
        image_urls = [f"/video-images/{path.name}" for path in image_paths]
        record = await self.video_repo.create_generation(
            user_id=user_id,
            generation_type="image_to_video",
            media_type="video",
            provider="runway",
            status="pending",
            prompt=prompt,
            style=style,
            aspect_ratio=aspect_ratio,
            voice_url=voice_url,
            source_image_url=image_urls[0] if image_urls else None,
            source_image_urls=image_urls,
            extra_data={"with_voice": True, "image_count": len(image_urls)},
        )
        try:
            await self.video_repo.mark_processing(record.id)
            ai_video_path = await self._generate_runway_image_to_video(
                image_paths=image_paths, prompt=prompt, style=style,
                aspect_ratio=aspect_ratio, duration=duration,
            )
            video_id = uuid.uuid4().hex
            filename = f"{video_id}.mp4"
            output_path = self.video_dir / filename
            await self._merge_video_and_voice(
                video_path=ai_video_path, voice_path=voice_path,
                output_path=output_path, aspect_ratio=aspect_ratio,
            )
            final_duration = self._get_video_duration(output_path)
            response = {
                "success": True,
                "message": "AI video generated successfully",
                "id": video_id,
                "record_id": record.id,
                "filename": filename,
                "video_url": f"/videos/{filename}",
                "generation_type": "image_to_video",
                "provider": "runway",
                "media_type": "video",
                "status": "completed",
                "voice_url": voice_url,
                "image_urls": image_urls,
                "image_count": len(image_urls),
                "image_url": image_urls[0],
                "prompt": prompt,
                "style": style,
                "aspect_ratio": aspect_ratio,
                "duration": final_duration,
                "voice_duration": voice_duration,
                "size": output_path.stat().st_size if output_path.exists() else 0,
                "created_at": datetime.now().isoformat(),
            }
            await self.video_repo.mark_done(
                record.id,
                output_url=response["video_url"],
                output_filename=filename,
                duration=final_duration,
                voice_url=voice_url,
                source_image_url=image_urls[0],
                source_image_urls=image_urls,
                extra_data={
                    "size": response["size"],
                    "voice_duration": voice_duration,
                    "image_count": len(image_urls),
                    "with_voice": True,
                },
            )
            return response
        except Exception as exc:
            await self.video_repo.mark_failed(record.id, str(exc))
            raise

    # ============================================================

    # RESPONSE HELPERS

    # ============================================================

    # ============================================================

    # RESPONSE HELPERS

    # ============================================================



    def _video_response(

        self,

        video_path: Path,

        *,

        generation_type: str,

        prompt: str,

        style: str,

        aspect_ratio: str,

    ) -> dict:

        return {

            "success": True,

            "id": video_path.stem,

            "filename": video_path.name,

            "video_url": f"/ai-videos/{video_path.name}",

            "generation_type": generation_type,

            "prompt": prompt,

            "style": style,

            "aspect_ratio": aspect_ratio,

            "duration": self._get_video_duration(video_path),

            "size": video_path.stat().st_size if video_path.exists() else 0,

            "created_at": datetime.now().isoformat(),

        }



    def _image_response(

        self,

        image_path: Path,

        *,

        generation_type: str,

        prompt: str,

        style: str,

        aspect_ratio: str,

    ) -> dict:

        return {

            "success": True,

            "id": image_path.stem,

            "filename": image_path.name,

            "image_url": f"/generated-images/{image_path.name}",

            "generation_type": generation_type,

            "prompt": prompt,

            "style": style,

            "aspect_ratio": aspect_ratio,

            "size": image_path.stat().st_size if image_path.exists() else 0,

            "created_at": datetime.now().isoformat(),

        }



    # ============================================================

    # GENERATED VIDEOS

    # ============================================================



    def _history_record_response(self, record) -> dict:
        extra_data = getattr(record, "extra_data", None) or {}
        return {
            "record_id": record.id,
            "id": record.id,
            "generation_type": getattr(record, "generation_type", None),
            "media_type": getattr(record, "media_type", None),
            "provider": getattr(record, "provider", None),
            "status": getattr(record, "status", None),
            "filename": getattr(record, "output_filename", None),
            "video_url": getattr(record, "output_url", None) if getattr(record, "media_type", None) == "video" else None,
            "image_url": getattr(record, "output_url", None) if getattr(record, "media_type", None) == "image" else None,
            "voice_url": getattr(record, "voice_url", None),
            "source_video_url": getattr(record, "source_video_url", None),
            "source_image_url": getattr(record, "source_image_url", None),
            "source_image_urls": getattr(record, "source_image_urls", None) or [],
            "reference_image_urls": getattr(record, "reference_image_urls", None) or [],
            "prompt": getattr(record, "prompt", None),
            "style": getattr(record, "style", None),
            "aspect_ratio": getattr(record, "aspect_ratio", None),
            "duration": getattr(record, "duration", None),
            "size": extra_data.get("size", 0),
            "error_message": getattr(record, "error_message", None),
            "extra_data": extra_data,
            "created_at": record.created_at.isoformat() if getattr(record, "created_at", None) else None,
            "updated_at": record.updated_at.isoformat() if getattr(record, "updated_at", None) else None,
        }

    async def get_generated_videos(self, user_id: uuid.UUID) -> dict:
        try:
            records = await self.video_repo.list_videos_by_user(user_id)
            videos = [self._history_record_response(record) for record in records]
            return {"success": True, "count": len(videos), "videos": videos}
        except Exception as exc:
            logger.exception("Failed to get generated videos from database")
            raise HTTPException(status_code=500, detail=f"Unable to load generated videos: {str(exc)}") from exc

    # ============================================================

    # GENERATED IMAGES

    # ============================================================

    # ============================================================

    # GENERATED IMAGES

    # ============================================================



    async def get_generated_images(self, user_id: uuid.UUID) -> dict:
        try:
            records = await self.video_repo.list_images_by_user(user_id)
            images = [self._history_record_response(record) for record in records]
            return {"success": True, "count": len(images), "images": images}
        except Exception as exc:
            logger.exception("Failed to get generated images from database")
            raise HTTPException(status_code=500, detail=f"Unable to load generated images: {str(exc)}") from exc

"""PNG loading, cached display sizes, pivots and explicit-frame clips."""

from dataclasses import dataclass
import logging

import pygame

from .asset_manifest import load_manifest
from .data_files import DataError, number


@dataclass(frozen=True)
class Sprite:
    surface: pygame.Surface
    pivot: tuple

    def blit(self, surface, anchor):
        width, height = self.surface.get_size()
        surface.blit(self.surface, (round(anchor[0] - width * self.pivot[0]),
                                    round(anchor[1] - height * self.pivot[1])))


@dataclass(frozen=True)
class Clip:
    frames: tuple
    fps: float
    loop: bool

    @property
    def duration(self):
        return len(self.frames) / self.fps

    def finished(self, age):
        return not self.loop and age >= self.duration

    def frame_at(self, age):
        index = int(max(0, age) * self.fps)
        return self.frames[index % len(self.frames) if self.loop else min(index, len(self.frames) - 1)]


@dataclass(frozen=True)
class SpriteBody:
    uid: str
    cell: tuple
    sprite: Sprite


class AssetManager:
    def __init__(self, root, definitions=()):
        self.manifest = load_manifest(root)
        self._images = {item.asset_id: item for item in self.manifest.images}
        self._animations = {item.asset_id: item for item in self.manifest.animations}
        self._visuals = {key: dict(states) for key, states in self.manifest.visuals}
        self._bindings = {item.definition_id: item.visual_id for item in definitions}
        for definition_id, visual_id in self._bindings.items():
            if visual_id not in self._visuals:
                raise DataError("{}: definition {}: unknown visual {}".format(root, definition_id, visual_id))
        self.clear_cache()
        # Validate all required files now, including unused entries.
        self.preload()

    @property
    def issues(self):
        return tuple(self._issues)

    def clear_cache(self):
        """Explicit development reload; no automatic filesystem checks per frame."""
        self._originals = {}
        self._scaled = {}
        self._sprites = {}
        self._clips = {}
        self._reported = set()
        self._issues = []

    def get_image(self, asset_id, scale=1):
        if number(scale, "image scale") <= 0:
            raise DataError("image scale must be positive")
        spec = self._images[asset_id]
        size = tuple(max(1, round(value * scale)) for value in spec.display_size)
        key = (asset_id, size)
        if key in self._sprites:
            return self._sprites[key]
        if spec.path not in self._originals:
            try:
                if pygame.display.get_surface() is None:
                    raise DataError("AssetManager requires an initialized display surface")
                self._originals[spec.path] = pygame.image.load(str(spec.path)).convert_alpha()
            except (OSError, ValueError, pygame.error) as error:
                if isinstance(error, DataError):
                    raise
                self._originals[spec.path] = str(error)
        original = self._originals[spec.path]
        if isinstance(original, str):
            message = "{} ({}): {}".format(asset_id, spec.path, original)
            if not spec.optional:
                raise DataError("required image unavailable: " + message)
            if asset_id not in self._reported:
                self._reported.add(asset_id)
                self._issues.append(message)
                logging.getLogger(__name__).warning("optional image unavailable: %s", message)
            self._sprites[key] = None
            return None
        image_key = (spec.path, size)
        if image_key not in self._scaled:
            self._scaled[image_key] = (original if size == original.get_size()
                                       else pygame.transform.smoothscale(original, size))
        sprite = Sprite(self._scaled[image_key], spec.pivot)
        self._sprites[key] = sprite
        return sprite

    def get_clip(self, asset_id, scale=1):
        if number(scale, "clip scale") <= 0:
            raise DataError("clip scale must be positive")
        key = (asset_id, scale)
        if key not in self._clips:
            spec = self._animations[asset_id]
            frames = tuple(self.get_image(frame, scale) for frame in spec.frames)
            self._clips[key] = Clip(frames, spec.fps, spec.loop) if all(frames) else None
        return self._clips[key]

    def visual(self, definition_id, state, scale=1):
        visual_id = self._bindings.get(definition_id)
        asset_id = self._visuals.get(visual_id, {}).get(state)
        if asset_id is None:
            return None
        if asset_id in self._images:
            image = self.get_image(asset_id, scale)
            return Clip((image,), 1, True) if image is not None else None
        return self.get_clip(asset_id, scale)

    def board_image(self, state, scale=1):
        asset_id = dict(self.manifest.board).get(state)
        return self.get_image(asset_id, scale) if asset_id else None

    def preload(self, scale=1):
        for asset_id in self._images:
            self.get_image(asset_id, scale)
        for asset_id in self._animations:
            self.get_clip(asset_id, scale)

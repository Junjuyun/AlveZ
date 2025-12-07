import os
import pygame


AUDIO_BASE = os.path.join(os.path.dirname(__file__), "Assets", "Sounds")


def load_sound(name: str):
    """Load a single sound from the shared audio folder."""
    path = os.path.join(AUDIO_BASE, name)
    if os.path.isfile(path):
        return pygame.mixer.Sound(path)
    return None


class AudioManager:
    def __init__(self):
        pygame.mixer.init()
        self.music_volume = 0.5
        self.sfx_volume = 0.8

        # SFX placeholders – wired up by the game on boot
        self.snd_pause = None
        self.snd_unpause = None
        self.snd_player_hit = None
        self.snd_player_death = None
        self.snd_enemy_death = None
        self.snd_shoot = None
        self.snd_level_up = None
        self.snd_game_over = None

        # Music paths
        self.music_menu = None
        self.music_ingame = None
        self.music_defeat = None

    def set_music_volume(self, v: float):
        self.music_volume = max(0.0, min(1.0, v))
        pygame.mixer.music.set_volume(self.music_volume)

    def set_sfx_volume(self, v: float):
        self.sfx_volume = max(0.0, min(1.0, v))

    def play_sfx(self, sound: pygame.mixer.Sound | None):
        if sound:
            sound.set_volume(self.sfx_volume)
            sound.play()

    def stop_music(self):
        pygame.mixer.music.stop()

    def play_music_file(self, music_path: str | None, loop: int = -1):
        if music_path:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play(loop)
            except Exception:
                # keep the game running even if a file fails to load
                pass

    def play_defeat_music(self):
        if self.music_defeat:
            self.play_music_file(self.music_defeat, loop=-1)


# global instance you can import
audio = AudioManager()

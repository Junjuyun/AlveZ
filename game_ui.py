import os
import pygame
from game_constants import COLOR_WHITE


# Try loading button container assets once at module import
_ASSET_DIR = os.path.join(os.path.dirname(__file__), "Assets", "Images")
_BTN_IMG_PATH = os.path.join(_ASSET_DIR, "button_container.png")
_BTN_PRESSED_PATH = os.path.join(_ASSET_DIR, "button_container_pressed.png")
try:
    _BTN_IMG = pygame.image.load(_BTN_IMG_PATH) if os.path.isfile(_BTN_IMG_PATH) else None
except Exception:
    _BTN_IMG = None
try:
    _BTN_PRESSED = pygame.image.load(_BTN_PRESSED_PATH) if os.path.isfile(_BTN_PRESSED_PATH) else None
except Exception:
    _BTN_PRESSED = None


def _draw_ninepatch(target_surf, img, rect, border=12):
    """Draw `img` into `rect` using a simple nine-patch (pixel-perfect scaling).
    `border` is the pixel thickness of the corners in the source image.
    """
    if img is None:
        return
    sw, sh = img.get_size()
    x, y, w, h = rect.x, rect.y, rect.w, rect.h

    # source rects
    left = border
    right = sw - border
    top = border
    bottom = sh - border

    # widths/heights of center/stretchable areas
    center_w = right - left
    center_h = bottom - top

    # destination splits
    dest_left = border
    dest_right = border
    dest_top = border
    dest_bottom = border

    # ensure center area non-negative
    dest_center_w = max(0, w - dest_left - dest_right)
    dest_center_h = max(0, h - dest_top - dest_bottom)

    # helper to blit a subregion scaled to destination
    def blit_region(sx, sy, swr, shr, dx, dy, dwr, dhr):
        sub = img.subsurface((sx, sy, swr, shr))
        if sub.get_size() != (dwr, dhr):
            sub = pygame.transform.smoothscale(sub, (dwr, dhr))
        target_surf.blit(sub, (dx, dy))

    # corners
    blit_region(0, 0, left, top, x, y, dest_left, dest_top)
    blit_region(right, 0, border, top, x + w - dest_right, y, dest_right, dest_top)
    blit_region(0, bottom, left, border, x, y + h - dest_bottom, dest_left, dest_bottom)
    blit_region(right, bottom, border, border, x + w - dest_right, y + h - dest_bottom, dest_right, dest_bottom)

    # edges
    # top edge
    if center_w > 0 and dest_center_w > 0:
        blit_region(left, 0, center_w, top, x + dest_left, y, dest_center_w, dest_top)
    # bottom edge
    if center_w > 0 and dest_center_w > 0:
        blit_region(left, bottom, center_w, border, x + dest_left, y + h - dest_bottom, dest_center_w, dest_bottom)
    # left edge
    if center_h > 0 and dest_center_h > 0:
        blit_region(0, top, left, center_h, x, y + dest_top, dest_left, dest_center_h)
    # right edge
    if center_h > 0 and dest_center_h > 0:
        blit_region(right, top, border, center_h, x + w - dest_right, y + dest_top, dest_right, dest_center_h)

    # center
    if center_w > 0 and center_h > 0 and dest_center_w > 0 and dest_center_h > 0:
        blit_region(left, top, center_w, center_h, x + dest_left, y + dest_top, dest_center_w, dest_center_h)


class Button:
    def __init__(self, rect, text, font, base_color, hover_color, active_color=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.base_color = base_color
        self.hover_color = hover_color
        self.active_color = active_color or hover_color

    def draw(self, surf):
        mouse_pos = pygame.mouse.get_pos()
        is_hover = self.rect.collidepoint(mouse_pos)
        is_pressed = is_hover and pygame.mouse.get_pressed()[0]

        # Use pressed asset for hover *and* pressed states (hover effect)
        img = _BTN_PRESSED if (is_pressed or is_hover) and _BTN_PRESSED is not None else _BTN_IMG
        if img is not None:
            _draw_ninepatch(surf, img, self.rect, border=8)
        else:
            color = self.active_color if is_pressed else (self.hover_color if is_hover else self.base_color)
            pygame.draw.rect(surf, color, self.rect, border_radius=8)

        # Render label and scale down for smaller button text
        BUTTON_TEXT_SCALE = 0.75
        label = self.font.render(self.text, True, COLOR_WHITE)
        if BUTTON_TEXT_SCALE != 1.0:
            new_w = max(1, int(label.get_width() * BUTTON_TEXT_SCALE))
            new_h = max(1, int(label.get_height() * BUTTON_TEXT_SCALE))
            try:
                label = pygame.transform.smoothscale(label, (new_w, new_h))
            except Exception:
                label = pygame.transform.scale(label, (new_w, new_h))

        surf.blit(
            label,
            (
                self.rect.centerx - label.get_width() // 2,
                self.rect.centery - label.get_height() // 2,
            ),
        )

    def is_clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )

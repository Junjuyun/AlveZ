import pygame
from settings import COLOR_WHITE


# =========================
# BUTTON
# =========================
class Button:
    def __init__(self, rect, text, font, base_color, hover_color):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.base_color = base_color
        self.hover_color = hover_color

    def draw(self, surf):
        mouse_pos = pygame.mouse.get_pos()
        is_hover = self.rect.collidepoint(mouse_pos)
        color = self.hover_color if is_hover else self.base_color
        pygame.draw.rect(surf, color, self.rect, border_radius=8)
        label = self.font.render(self.text, True, COLOR_WHITE)
        surf.blit(
            label,
            (
                self.rect.centerx - label.get_width() // 2,
                self.rect.centery - label.get_height() // 2,
            ),
        )

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False
from typing import Tuple
import pygame as pg
from battle_tanks import ROUTE

FONT = ROUTE("assets/Pixel Digivolve.otf")

class TextComponent:

    """Surface for text rendering """
    def __init__(self, position, text, color=None, font_size=32, outline_color=None):
        self._color = color if color is not None else (160, 0, 0)
        self.size_font = font_size
        self._outline_color = outline_color
        self._text = text
        
        self._surface = self.render(self._text, FONT, self._color, self.size_font, self._outline_color)
        self._rect = self._surface.get_rect()
        self._rect.center = position

    @staticmethod
    def render(text: str, font_path: str, color: Tuple[int, int, int], size: int, outline_color=None):
        """ Render text with an optional outline """
        font = pg.font.Font(font_path, size)
        base_text = font.render(text, True, color)
    
        if outline_color is None:
            return base_text
        
        out_img = font.render(text, True, outline_color)
        w, h = base_text.get_size()
        outline_surf = pg.Surface((w + 2, h + 2), pg.SRCALPHA)
    
        outline_surf.blit(out_img, (0, 3))
        outline_surf.blit(out_img, (2, 3))
        outline_surf.blit(out_img, (3, 0))
        outline_surf.blit(out_img, (3, 2))
        outline_surf.blit(base_text, (3, 3))
    
        return outline_surf    

    def update(self):
        """ Updates the surface and maintains centering """
        old_center = self._rect.center
        self._surface = self.render(self._text, FONT, self._color, self.size_font, self._outline_color)
        self._rect = self._surface.get_rect()
        self._rect.center = old_center

    @property
    def color(self):
        """getter color"""
        return self._color

    @color.setter
    def color(self, color: Tuple[int, int, int]):
        """Update color and maintain centering/outline"""
        self._color = color
        center = self._rect.center
        self._surface = self.render(self._text, FONT, self._color, self.size_font, self._outline_color)
        self._rect = self._surface.get_rect(center=center)

    @property
    def text(self):
        """getting """
        return self._text
        
    @text.setter
    def text(self, text):
        """Update text and maintain centering/outline"""
        center = self._rect.center
        self._text = text
        self._surface = self.render(self._text, FONT, self._color, self.size_font, self._outline_color)
        self._rect = self._surface.get_rect(center=center)

    def draw(self,screen):
        """ draw"""
        screen.blit(self._surface,self._rect)

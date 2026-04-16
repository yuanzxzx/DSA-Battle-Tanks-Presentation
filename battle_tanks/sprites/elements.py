import pygame as pg
from battle_tanks import ROUTE


class SpriteBasic(pg.sprite.Sprite):
    def __init__(self, x_pos,y_pos,width,height):
        super().__init__()
        self._data = None
        self.rect = pg.Rect((x_pos, y_pos), (width, height))


    @classmethod
    def boom(cls):
        pass
        # cls.SOUND_BOOM.play()


    @property
    def data(self):
        return self._data


    @data.setter
    def data(self, data: bytes):
       self._data = data


class Brick(SpriteBasic):
    """Class representing a Brick object"""
    def __init__(self,x_pos,y_pos,width,height):
        super().__init__(x_pos,y_pos,width,height)
        self.box_img = pg.image.load(ROUTE("assets/images/tiles.png"))
        self.image = self.box_img.subsurface((0,0),(32,32))


class Block(SpriteBasic):
    """ Class representing a Block object """
    def __init__(self,x_pos,y_pos,width,height):
        super().__init__(x_pos,y_pos,width,height)

class Particle(pg.sprite.Sprite):
    """Particle effect for wall destruction"""
    def __init__(self, x, y, vx, vy, color=(139, 69, 19), lifetime=30):
        super().__init__()
        self.rect = pg.Rect(x, y, 4, 4)
        self.vx = vx
        self.vy = vy
        self.color = color
        self.lifetime = lifetime
        self.age = 0
        self.image = pg.Surface((4, 4), pg.SRCALPHA)
        self._update_image()

    def _update_image(self):
        alpha = int(255 * (1 - self.age / self.lifetime))
        self.image.fill((0, 0, 0, 0))
        pg.draw.circle(self.image, (*self.color, alpha), (2, 2), 2)

    def update(self):
        self.age += 1
        self.rect.x += self.vx
        self.rect.y += self.vy
        self.vy += 0.1  # gravity
        self._update_image()
        if self.age >= self.lifetime:
            self.kill()

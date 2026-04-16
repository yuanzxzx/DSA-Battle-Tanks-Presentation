import math
import pygame as pg


class Bullet(pg.sprite.Sprite):
    SPEED = 8
    MAX_DISTANCE = 500
    SIZE = 8

    def __init__(self, start_pos: tuple[int, int], angle: float):
        super().__init__()
        self.angle = angle
        self._distance_traveled = 0
        
        # Create a simple circular bullet sprite (same from all angles)
        self.image = pg.Surface((self.SIZE, self.SIZE), pg.SRCALPHA)
        pg.draw.circle(self.image, (255, 200, 0), (self.SIZE // 2, self.SIZE // 2), self.SIZE // 2)
        
        self.rect = self.image.get_rect(center=start_pos)

        # Match collision.py direction: (-sin(angle), -cos(angle))
        radian = math.radians(self.angle)
        self.vx = -math.sin(radian) * self.SPEED
        self.vy = -math.cos(radian) * self.SPEED

    def update(self, bounds_rect: pg.Rect):
        self.rect.x += self.vx
        self.rect.y += self.vy
        self._distance_traveled += self.SPEED

        if not bounds_rect.colliderect(self.rect) or self._distance_traveled >= self.MAX_DISTANCE:
            self.kill()

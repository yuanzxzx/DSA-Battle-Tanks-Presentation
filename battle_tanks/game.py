#!/usr/bin/python3
""" this is the manager game """

import sys
import math
from typing import Tuple, Dict, Union, List
import pygame as pg
import random

from battle_tanks.commons.package import Struct, Collision
from battle_tanks.components.movement import MovementComponent
from battle_tanks.components.tile_map import TileMap
from battle_tanks.components.camera import CameraComponent
from battle_tanks.sprites import Player, Brick

from battle_tanks.sprites.elements import Particle
from battle_tanks.commons.municion import CannonType
from battle_tanks.commons.tank_surface import tank_cover
from battle_tanks.components.network import NetworkComponent
from battle_tanks import ROUTE



type_guns = {
    "MEDIUM": CannonType(20,"MEDIUM",(8,10)),
}
pg.mixer.init()
SOUND_BOOM = pg.mixer.Sound(ROUTE("assets/sound/boom.wav"))
SHOT = pg.mixer.Sound(ROUTE("assets/sound/shot.wav"))
BG_TRACK = pg.mixer.music.load(ROUTE("assets/sound/bg_track.wav"))
pg.mixer.music.play(-1)

SOUND_BOOM.set_volume(0.1)
SHOT.set_volume(0.1)
pg.mixer.music.set_volume(0.5)




def find_sprite(rect: pg.Rect, group: pg.sprite.Group) -> Union[pg.sprite.Sprite, bool]:
    for sprite in group:
        if sprite.rect.colliderect(rect):
            return sprite
    return False


class Game:
    def __init__(self,
                 addr:Union[Tuple[str,int], None],
                 screen:pg.Surface,
                 player_name="John",
                 tank_color:int=0):
        
        self.laser_timers = {}

        self.network = NetworkComponent(addr, player_name, tank_color) if addr is not None else None
        self._player_number = self.network.player_number if addr is not None else 0
        self.tank_color = tank_color
        self.positions = {}


        pg.display.set_caption(f"Battle Tank - Client: {self._player_number} - User: {player_name}")


        self.WIDTH,self.HEIGHT = screen.get_size()
        self.SCREEN = screen

        self.tile = TileMap(self.network.lvl_map)
        self.tile_image = self.tile.make_map()
        self.tile_rect = self.tile_image.get_rect()

        self.players: Dict[int,Player] = {}
        self._bricks = pg.sprite.Group()
        self._particles = pg.sprite.Group()
        self._damage = 0
                     

        if self.network and self.network.player_data != Struct.USER_NOT_AVAILABLE:
            position = (self.network.player_data["x"],self.network.player_data["y"])
        else:
            position = (0,0)

        self.player = Player(position, self._player_number, cannon_type=type_guns.get("MEDIUM"), tank_color=tank_color)
        self.players[self._player_number] = self.player
        self.camera = CameraComponent(self.tile.WIDTH, self.tile.HEIGHT, (self.WIDTH, self.HEIGHT))
        self.move = MovementComponent(self.network, self.player)
        self.load()

        self._font = pg.font.Font(None, 24)  
        self.notifications = []

    def add_notification(self, text: str, duration: int = 120):
        self.notifications.append({"text": text, "timer": duration})


    @property
    def damage(self):
        """ return damage from player """
        return self.player.damage
    
    def _spawn_particles(self, x, y, count=8):
        """Spawn particles at brick destruction location"""
        import math
        import random
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 5)
            vx = speed * math.cos(angle)
            vy = speed * math.sin(angle)
            particle = Particle(x, y, vx, vy, color=(139, 69, 19))
            self._particles.add(particle)

    def load(self):
        for data_sprite in self.network.get_events_to_game_state():
            if data_sprite[0] == Struct.BRICK:
                brick = Brick(data_sprite[1],data_sprite[2],data_sprite[3],data_sprite[4])
                self._bricks.add(brick)
                Collision.bricks.add(brick)  # Also add to collision system


            
    def break_brick_locally(self, brick):
        """Handles the local visual removal of a brick."""
        if brick in self._bricks:
            self._bricks.remove(brick)
            Collision.bricks.remove(brick)
            self._spawn_particles(brick.rect.centerx, brick.rect.centery)
            SOUND_BOOM.play()
            brick.kill()

    def send_brick_break_to_server(self, brick):
        """Informs the network that a brick has been destroyed."""
        if self.network:
            event_data = Struct.pack_tile({
                "type": Struct.BROKE_BRICK,
                "x": brick.rect.x,
                "y": brick.rect.y,
                "w": brick.rect.w,
                "h": brick.rect.h
            })
            self.network.send_move_tcp(event_data)
    def update(self):
        """ Update Game"""
        self._particles.update()
        dt = 1/60
                
        """ SEND MOVES BYTES """
        self.move.keys()
        """ MOVES RESPONSE """

        if self.network:
            recv_all:List[dict] = self.network.recv_to_queue()

            for recv in recv_all:
                if (recv.get("status") == Struct.NEW_PLAYER or
                        recv.get("status") == Struct.OLD_PLAYER):
                    position = recv["position"]
                    tank_color = recv.get("tank_color", 0)
                    player = Player((recv["x"],recv["y"]), position, cannon_type = type_guns.get("BASIC"), tank_color=tank_color)
                    player.name = recv.get("name", f"Player {position}")  # Establecer el nombre del jugador
                    self.players[position] = player

                elif recv.get("status") in (Struct.UPDATE_PLAYER, Struct.PLAYER_SHOT):
                    position = recv["position"]
                    
                    if self.players.get(position):
                        player = self.players[position]
                        old_damage = player.damage

                        player.rect.x = recv["x"]
                        player.rect.y = recv["y"]

                        player.body_rect.x = player.rect.x
                        player.body_rect.y = player.rect.y

                        player.rect_cannon.center = player.body_rect.center

                        player.angle = recv["angle"]
                        player.angle_cannon = recv["angle_cannon"]
                        player.damage = recv["damage_indicator"]
                        
                        # Camera shake when the player takes damage
                        if recv["damage_indicator"] > old_damage and player.player_number == self._player_number:
                            self.camera.shake(duration=12, intensity=5)
                        
                        player.laser_active = recv.get("laser_active", getattr(player, "laser_active", False))

                    

                    else:
                        tank_color = recv.get("tank_color", 0)
                        player = Player((recv["x"], recv["y"]), position, cannon_type=type_guns.get("BASIC"), tank_color=tank_color)
                        player.name = recv.get("name", f"Player {position}")  # Establecer el nombre del jugador
                        self.players[position] = player

                elif recv.get("status") == Struct.BROKE_BRICK:
                    brick_rect = pg.Rect(recv["x"], recv["y"], recv["w"], recv["h"])
                    sprite_brick = find_sprite(brick_rect, self._bricks)
                    if sprite_brick:
                        self._bricks.remove(sprite_brick)
                        self._spawn_particles(sprite_brick.rect.centerx, sprite_brick.rect.centery)
                        SOUND_BOOM.play()
                        sprite_brick.kill()
                        
                    collision_brick = find_sprite(brick_rect, Collision.bricks)
                    if collision_brick:
                        Collision.bricks.remove(collision_brick)

                elif recv.get("status") == Struct.BLOCK:
                    Brick.boom() 



        self.camera.update(self.player)

    def draw(self, main_screen: pg.Surface):
        """ Draw the player and scene. """
        # 1. DRAW BACKGROUND
        self.SCREEN.blit(self.tile_image,self.camera.apply_rect(self.tile_rect))

        # 2. DRAW PLAYERS, LASERS, AND UI BARS
        for _,player in self.players.items():
            # Dibujar el tanque
            tank_rect = self.camera.apply(player)
            tank_cover(player.tank_color, tank_rect, self.SCREEN, angle=player.angle,
                       angle_cannon=player.angle_cannon)
            
            if getattr(player, "laser_active", False):
                import math
                rad_angle = math.radians(-player.angle_cannon - 90)
                
                barrel_offset = 20 
                start_pos = (
                    tank_rect.centerx + barrel_offset * math.cos(rad_angle),
                    tank_rect.centery + barrel_offset * math.sin(rad_angle)
                )
                
                end_pos = (start_pos[0] + 300 * math.cos(rad_angle), 
                           start_pos[1] + 300 * math.sin(rad_angle))
                
                pg.draw.line(self.SCREEN, (255, 50, 50), start_pos, end_pos, 5)
                pg.draw.line(self.SCREEN, (255, 255, 255), start_pos, end_pos, 2) 

            # Dibujar el nombre del jugador
            font = pg.font.Font(None, 24)  
            text_surface = font.render(player.name, True, (255, 255, 255))  
            text_rect = text_surface.get_rect()
            
            text_rect.centerx = tank_rect.centerx
            text_rect.bottom = tank_rect.top - 5  
            self.SCREEN.blit(text_surface, text_rect)

            # Dibujar la barra de vida
            health_width = 50  
            health_height = 5  
            health_x = tank_rect.centerx - health_width // 2
            health_y = text_rect.bottom + 2  

            pg.draw.rect(self.SCREEN, (100, 100, 100), 
                        (health_x, health_y, health_width, health_height))
            
            health_percentage = 1 - (player.damage / Player.MAX_DAMAGE)
            current_health_width = int(health_width * health_percentage)
            
            pg.draw.rect(self.SCREEN, (255, 0, 0), 
                        (health_x, health_y, current_health_width, health_height))

            if player.player_number == self._player_number:
                energy_y = health_y + health_height + 2 
                
                pg.draw.rect(self.SCREEN, (50, 50, 50), 
                            (health_x, energy_y, health_width, health_height))
                
                current_energy = getattr(player, "laser_energy", 100)
                current_energy_width = int(health_width * (current_energy / 100))
                
                pg.draw.rect(self.SCREEN, (0, 255, 255), 
                            (health_x, energy_y, current_energy_width, health_height))

        for brick in self._bricks:
            self.SCREEN.blit(brick.image, self.camera.apply(brick))

        for particle in self._particles:
            self.SCREEN.blit(particle.image, self.camera.apply(particle))
    
        telescopic_pos = Collision.calculate_bullet_position(self.player.telescopic_sight(), 100)
        telescopic_rect = self.camera.apply_rect(pg.rect.Rect(telescopic_pos[0],telescopic_pos[1],20,20))
        self.SCREEN.blit(Player.TELESCOPIC_SIGH, telescopic_rect)

        y_offset = 60 
        for notif in getattr(self, "notifications", [])[:]:
            if notif["timer"] > 0:
                alpha = min(255, notif["timer"] * 4) 
                
                notif_surface = self._font.render(notif["text"], True, (255, 255, 0))
                notif_surface.set_alpha(alpha) 
                
                notif_rect = notif_surface.get_rect(center=(self.WIDTH // 2, y_offset))
                
                bg_rect = notif_rect.inflate(20, 10)
                pg.draw.rect(self.SCREEN, (0, 0, 0, 150), bg_rect, border_radius=5)
                self.SCREEN.blit(notif_surface, notif_rect)
                
                notif["timer"] -= 1
                y_offset += 35 
            else:
                self.notifications.remove(notif)

        main_screen.blit(self.SCREEN, (0,0))
        

    def close(self):
        if self.network:
            self.network.socket_tcp.send(Struct.CLOSE_CONN)
            self.network.socket_tcp.close()
        pg.quit()
        sys.exit()


    def __str__(self):
        return (f"\n\nPlayer Number: {self._player_number} "
                f"\nPlayer Name: {self.network.name} "
                f"\nStatus: {'Multiplayer' if self.network.addr else 'Single'}\n\n")

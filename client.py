""" Client and Single Game"""

import pygame as pg
import queue 
import threading as th
import math
import time
from typing import Tuple, List

from battle_tanks.components.text import TextComponent
from battle_tanks import  ROUTE
from battle_tanks.commons.package import Struct
from battle_tanks.components import NetworkComponent
from battle_tanks.menu import Menu


"""------Burst Algorithm Start------"""
BURST_ICON = pg.image.load(ROUTE("assets/images/burst_icon.png"))
BURST_ICON = pg.transform.scale(BURST_ICON, (60, 60))

def handle_burst_fire(game, menu):
    """
    Instantly triggers a 5-bullet burst and 15s cooldown upon pressing 'K'.
    """
    # Initialize variables on player if not already there
    if not hasattr(game.player, 'last_burst_time'):
        game.player.last_burst_time = 0
        game.player.burst_cooldown = 15.0 
        game.player.can_burst = True  # Toggle to ensure one trigger per press

    current_time = time.time()
    keys = pg.key.get_pressed()

    # 1. Check if the 15s cooldown has passed
    cooldown_elapsed = current_time - game.player.last_burst_time >= game.player.burst_cooldown

    # 2. Shooting Trigger for "K"
    if keys[pg.K_k] and menu.select_option is not None:
        # Trigger only if cooldown is done AND it's a fresh press
        if cooldown_elapsed and game.player.can_burst:
            # Instantly fire 5 bullets
            for _ in range(5):
                if game.player.check_available_bullets():
                    game.player.fire = True 
                    game.network.send_move_tcp(Struct.FIRE_EVENT_PLAYER)
            
            # Start cooldown immediately
            game.player.last_burst_time = current_time
            game.player.can_burst = False # Lock until key is released
    else:
        # Reset the toggle when the key is released
        game.player.can_burst = True

def draw_burst_indicator(screen, game, x, y):
    """
    Draws the 'K' icon with a circular red cooldown overlay.
    """
    current_time = time.time()
    
    # Calculate cooldown progress percentage
    time_passed = current_time - game.player.last_burst_time
    progress = min(time_passed / game.player.burst_cooldown, 1.0)
    
    # Draw the base K icon
    screen.blit(BURST_ICON, (x, y))
    
    # If cooling down, draw the red progress arc
    # The arc shows as long as the 15-second window hasn't finished
    if progress < 1.0:
        rect = pg.Rect(x, y, 60, 60)
        # Start at top (-90 deg) and draw the remaining slice
        start_angle = math.radians(-90 + (progress * 360))
        stop_angle = math.radians(270)
        pg.draw.arc(screen, (255, 0, 0), rect, start_angle, stop_angle, 5)
"""------Burst Algorithm End------"""


def network_client_consumer(client: NetworkComponent):
    """
    Waits for responses from the server and sends the results to the update queue.
    """
    while True:
        # Receive data from the server
        data = client.recv_move_player()
        
        # Put the received data into the update queue
        NetworkComponent.UPDATE_Q.put(data)


def network_client_handler(client: NetworkComponent):
    """
    Handles network communication for a client.
    """
    while True:
        # Get an item from the SEND_Q queue
        data = NetworkComponent.SEND_Q.get()
        
        # If the item is not queue.Empty, send the move to the server
        if data is not queue.Empty:
            client.send_move_tcp(data)
        


def main():
    """ Client game of server"""

    pg.display.set_caption(f"Battle Tank")
    pg.display.set_icon(pg.image.load(ROUTE("lemon.ico")))
    pg.font.init()
    pg.event.set_allowed([
        pg.QUIT,
        pg.KEYDOWN,
        pg.KEYUP,
    ])

    clock = pg.time.Clock()
    WIDTH,HEIGHT = 800, 600
    SCREEN = pg.display.set_mode((WIDTH,HEIGHT + 36))

    main_game = pg.Surface((WIDTH,HEIGHT))
    menu = Menu(SCREEN)
    game = menu.update(main_game)
    text_damage = TextComponent((WIDTH//2,HEIGHT +16 ),f"Damage: {game.damage} %")
    bullets = pg.Surface((WIDTH,36))



    """
    CLIENT NETWORK
    """
    th_recevied = th.Thread(target = network_client_consumer, daemon = True, args= (game.network,))
    th_send = th.Thread(target = network_client_handler, daemon = True, args=(game.network,))

    th_recevied.start()
    th_send.start()




    while True:
        handle_burst_fire(game, menu)
        """Burst indicator ^"""
        for event in pg.event.get():
            if event.type == pg.QUIT:
                game.close()
            elif event.type == pg.KEYUP:
                key = event.dict.get("key")
                if key == pg.K_o and menu.select_option is not None:
                    if game.player.check_available_bullets():
                        game.player.fire = True
                        game.network.send_move_tcp(Struct.FIRE_EVENT_PLAYER)

            
        SCREEN.fill((0,0,0))
        game.update()
        game.draw(SCREEN)
        draw_burst_indicator(SCREEN, game, WIDTH - 80, HEIGHT - 80)
        """Burst indicator on screen ^"""

        bullets.fill((0,50,0))
        game.player.type_gun.render(bullets)
        SCREEN.blit(bullets,(0,HEIGHT))


        text_damage.text = f"Damage: {game.damage} %"
        text_damage.update()
        text_damage.draw(SCREEN)

        """
        TICKS IN CLIENT
        """
        clock.tick(60)
        pg.display.flip()

if __name__ == "__main__":
    main()

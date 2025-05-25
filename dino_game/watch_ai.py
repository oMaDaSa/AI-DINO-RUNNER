import pygame
import settings
from dino import Dino
from base_game import BaseAIGame
import numpy as np

class Watch(BaseAIGame):
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)

        self.dino = Dino(x=50, y=settings.GROUND_LEVEL + 60) 
        self.sprites.add(self.dino)


    def update_game_state(self):
        if self.game_over:
            return

        # passo 1: ai pega o estado atual e escohe ação
        self.dino.cast_rays(self.obstacles) 
        current_state = self.get_state(self.dino)
        action = self.choose_action(current_state)

        # paso 2: ai faz a ação
        self.perform_action(self.dino, action)
        
        # passo 3: atualiza o mundo
        # passo 4: spawn de obstaculos
        super().update_game_state()

        # passo 5: checa colisoes
        self.check_collisions(self.dino)


    def reset_game(self):
        super().reset_game()
        self.dino.reset()

if __name__ == '__main__':
    pygame.init()

    screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
    pygame.display.set_caption("Dino AI Watch Mode (Simplified)")

    game_instance = Watch(screen=screen)
    game_instance.run()

    pygame.quit()
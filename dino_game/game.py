import pygame
import settings
from dino import Dino
from base_game import BaseGame

class Game(BaseGame):
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        self.dino = Dino(x=50, y=settings.GROUND_LEVEL+60)
        self.sprites.add(self.dino)
    
    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if self.game_over:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r: 
                        self.reset_game()
                    elif event.key == pygame.K_ESCAPE: 
                        self.running = False
                return

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    self.dino.jump()
                elif event.key == pygame.K_DOWN:
                    self.dino.crouch()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_DOWN:
                            self.dino.stand()

    def update_game_state(self):
        if self.game_over:
            return 

        super().update_game_state()
        if self.check_collisions(self.dino):
            self.game_over = True
        self.score += 1


    def draw_game(self):
        super().draw_game()

        if self.game_over:
            restart_text = self.small_font.render("'R' - Restart | ESC - Menu", True, (200,200,200))
            restart_rect = restart_text.get_rect(center=(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2 + 50))
            self.screen.blit(restart_text, restart_rect)

    def reset_game(self):
        super().reset_game()
        self.dino.reset()
    
if __name__ == '__main__':
    pygame.init()
    
    test_screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))

    game_instance = Game(screen=test_screen)
    
    game_instance.run()

    pygame.quit()
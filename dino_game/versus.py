import pygame
import settings
from dino import Dino
from base_game import BaseAIGame

class Versus(BaseAIGame):
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)

        # Player - controles por input
        self.player_dino = Dino(x=50, y=settings.GROUND_LEVEL + 60)
        self.player_dino.is_player = True
        self.sprites.add(self.player_dino)
        
        # AI  - controlado pela q-table e get_state
        self.ai_dino = Dino(x=50, y=settings.GROUND_LEVEL + 60, alpha=180)
        self.ai_dino.color = settings.COLOR_VERSUS
        self.ai_dino.is_player = False
        self.sprites.add(self.ai_dino)
        
        # estados
        self.player_alive = True
        self.ai_alive = True
        self.versus_result = ""

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
                    self.player_dino.jump()
                elif event.key == pygame.K_DOWN:
                    self.player_dino.crouch()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_DOWN:
                            self.player_dino.stand()

    def update_game_state(self):
        if self.game_over:
            return

        #decisão da IA
        if self.ai_alive:
            self.ai_dino.cast_rays(self.obstacles)
            current_state = self.get_state(self.ai_dino)
            action = self.choose_action(current_state)
            self.perform_action(self.ai_dino, action)
        
        #atualiza estado do jogo
        super().update_game_state()
        
        #checa colisao
        # colisão pro player
        if super().check_collisions(self.player_dino):
            self.player_alive = False
            self.versus_result = "The AI outlasted you!" if self.ai_alive else "You survived longer than the AI!"

        # colisão pra ia
        if super().check_collisions(self.ai_dino):
            self.ai_alive = False
        
        # game over quando player morre
        if not self.player_alive:
            self.game_over = True

    def draw_game(self):
        # Draw background, ground, obstacles using parent method
        self.screen.fill(settings.COLOR_SKY)
        pygame.draw.rect(self.screen, settings.COLOR_GROUND, pygame.Rect(0, settings.GROUND_LEVEL, settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT - settings.GROUND_LEVEL))
        
        #  obstaculos
        for obstacle in self.obstacles:
            obstacle.draw(self.screen)

        if self.ai_alive:
            self.ai_dino.draw(self.screen)
            # AI name
            ai_text = self.small_font.render("AI", True, settings.COLOR_VERSUS)
            self.screen.blit(ai_text, (self.ai_dino.rect.centerx - 10, self.ai_dino.rect.top - 25))

        
        if self.player_alive:
            self.player_dino.draw(self.screen)
            # Player name
            player_text = self.small_font.render("Player", True, settings.COLOR_DINO)
            self.screen.blit(player_text, (self.player_dino.rect.centerx - 25, self.player_dino.rect.top - 25))
            
        
        
        # score
        super().draw_info()
        
        if self.game_over:
            self.draw_game_over()

    def draw_game_over(self):
        super().draw_game_over()
        result = self.font.render(self.versus_result, True, (255, 255, 255))
        self.screen.blit(result, result.get_rect(center=(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2 - 80)))
        
    def reset_game(self):
        super().reset_game()
        self.player_dino.reset()
        self.ai_dino.reset()
        self.player_alive = True
        self.ai_alive = True
        self.versus_result = ""

if __name__ == '__main__':
    pygame.init()

    test_screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))

    game_instance = Versus(screen=test_screen)
    game_instance.run()

    pygame.quit()

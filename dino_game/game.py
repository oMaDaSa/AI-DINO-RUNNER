import pygame
import settings
from dino import Dino
from obstacle import Obstacle

class Game:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        self.running = False
        self.game_over = False
        self.score = 0
        self.high_score = 0 #TODO: implementar armazenamento
        
        self.sprites = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()

        self.dino = Dino(x=50, y=settings.GROUND_LEVEL+60)
        self.sprites.add(self.dino)

    def spawn_obstacle(self):
        obstacle = Obstacle()
        self.sprites.add(obstacle)
        self.obstacles.add(obstacle)
    
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

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    self.dino.jump()

    def update_game_state(self):
        if self.game_over:
            return 

        self.sprites.update()

        self.obstacle_spawn_timer += 1
        if self.obstacle_spawn_timer >= 100:
            self.spawn_obstacle()
            self.obstacle_spawn_timer = 0 # Reset timer
            
        hit_obstacles = pygame.sprite.spritecollide(self.dino, self.obstacles, False, pygame.sprite.collide_rect)
        if hit_obstacles:
            self.game_over = True 
           
        self.score += 1/settings.FPS


    def draw_game(self):
        self.screen.fill(settings.SKY_BLUE)
        pygame.draw.rect(self.screen, settings.GROUND_BROWN, pygame.Rect(0, settings.GROUND_LEVEL, settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT - settings.GROUND_LEVEL))
       
        for entity in self.sprites:
            entity.draw(self.screen)

        score_text = self.font.render(f"Score: {int(self.score)}", True, settings.TEXT_COLOR)
        self.screen.blit(score_text, (10, 10))


        if self.game_over:
            overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128)) # 50% opacidade
            self.screen.blit(overlay, (0,0))

            game_over_text = self.font.render("Game Over", True, (255,255,255)) 
            text_rect = game_over_text.get_rect(center=(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2 - 30))
            self.screen.blit(game_over_text, text_rect)
            
            final_score_text = self.small_font.render(f"Final Score: {self.score}", True, (255,255,255))
            score_rect = final_score_text.get_rect(center=(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2 + 10))
            self.screen.blit(final_score_text, score_rect)

            restart_text = self.small_font.render("'R' - Restart | ESC - Menu", True, (200,200,200))
            restart_rect = restart_text.get_rect(center=(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2 + 50))
            self.screen.blit(restart_text, restart_rect)

        pygame.display.flip()

    def reset_game(self):
        self.score = 0
        self.game_over = False
        self.obstacle_spawn_timer = 0

        self.dino.reset()
        for obstacle in self.obstacles:
            obstacle.kill()

    def run(self):
        self.running = True
        self.reset_game()

        while self.running:
            self.handle_input()     
            self.update_game_state() 
            self.draw_game()        
            
            self.clock.tick(settings.FPS)     
        
        return self.score 
    

if __name__ == '__main__':
    pygame.init()
    
    test_screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))

    game_instance = Game(screen=test_screen)
    
    game_instance.run()

    pygame.quit()
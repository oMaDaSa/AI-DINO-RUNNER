import pygame
import settings
from dino import Dino
from obstacle import Obstacle
import random
import math

class Training:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.last_spawn = pygame.time.get_ticks()

        self.running = False
        self.game_over = False
        self.score = 0
        self.high_score = 0 #TODO: implementar armazenamento
        
        #População
        self.population_size = settings.POPULATION_SIZE
        self.dinos = pygame.sprite.Group()
        self.active_dino_count = 0
        self.best_dino = None
        self.best_fitness = 0
        self.generation = 1

        #Detecção de obstaculos
        self.obstacle_detection = {
            'ground_detected': False,
            'flying_detected': False,
            'ground_distance': float('inf'),
            'flying_ditance': float('inf')
        }

        self.sprites = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()

        for i in range(self.population_size):
            alpha = 25 #semi transparente
            dino = Dino(x = 50, y = settings.GROUND_LEVEL + 60, alpha = alpha, dino_id = i)
            self.dinos.add(dino)
            self.sprites.add(dino)

        self.dino = list(self.dinos)[0]
        self.active_dino_count = self.population_size
        self.obstacle_spawn_timer = 0

    def detect_obstacle(self, dino):
        ground_obstacle_detected = False
        flying_obstacle_detected = False
        closest_ground_obstacle_distance = float('inf')
        closest_flying_obstacle_distance = float('inf')

        for i, ray in enumerate(dino.rays):
            if ray['hit']:
                angle = settings.RAY_ANGLES[i]

                if ray['obstacle_type'] == 'ground':
                    ground_obstacle_detected = True
                    if ray['distance'] < closest_ground_obstacle_distance:
                        closest_ground_obstacle_distance = ray['distance']
                elif ray['obstacle_type'] == 'flying':
                    flying_obstacle_detected = True
                    if ray['distance'] < closest_flying_obstacle_distance:
                        closest_flying_obstacle_distance = ray['distance']
        return {
            'ground_detected':ground_obstacle_detected,
            'flying_detected':flying_obstacle_detected,
            'ground_distance':closest_ground_obstacle_distance,
            'flying_distance':closest_flying_obstacle_distance,
        }

    def spawn_obstacle(self):
        is_flying = random.randint(0,1)
        obstacle = Obstacle(is_flying = is_flying)
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

    def update_game_state(self):
        if self.active_dino_count == 0 or self.game_over:
            return 
        

        for dino in self.dinos:
            if not dino.is_alive:
                continue
            
            dino.cast_rays(self.obstacles)

            choice = random.random()
            if choice < 0.1: dino.jump()
            elif choice < 0.3: dino.crouch()
            else: dino.stand()

        self.sprites.update()

        Obstacle.GLOBAL_SPEED -= settings.SPEED_INCREASE

        spawn_interval = max(300, settings.SPAWN_INTERVAL + Obstacle.GLOBAL_SPEED)

        current_time = pygame.time.get_ticks()

        if current_time - self.last_spawn >= spawn_interval:
            self.spawn_obstacle()
            self.last_spawn = current_time
            
        hit_obstacles = pygame.sprite.spritecollide(self.dino, self.obstacles, False, pygame.sprite.collide_rect)

        self.active_dino_count = 0
        for dino in self.dinos:
            if not dino.is_alive:
                continue

            self.active_dino_count += 1
            hit_obstacles = pygame.sprite.spritecollide(dino, self.obstacles, False, pygame.sprite.collide_rect)
            if hit_obstacles:
                dino.die()
                self.active_dino_count -= 1

        if self.active_dino_count == 0:
            self.game_over = True
            return
           
        self.score += 1/settings.FPS


    def draw_game(self):
        self.screen.fill(settings.SKY_BLUE)
        pygame.draw.rect(self.screen, settings.GROUND_BROWN, pygame.Rect(0, settings.GROUND_LEVEL, settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT - settings.GROUND_LEVEL))
       
        for entity in self.sprites:
            if isinstance(entity, Dino):
                if entity.is_alive:  # só os dinossauros vivos
                    entity.draw(self.screen)
            else:
                entity.draw(self.screen)

        for dino in self.dinos:
            if dino.is_alive:
                for i, ray in enumerate(dino.rays):
                    # Cor diferente baseado no obstaculo atingido
                    if not ray['hit']:
                        ray_color = (255, 0, 0) # vermelho para nada
                    elif ray['obstacle_type'] == 'ground':
                        ray_color = (0, 255, 0)  # verde para cactus
                    elif ray['obstacle_type'] == 'flying':
                        ray_color = (255, 165, 0)  # laranja pra voador
                    else:
                        ray_color = (0, 0, 0) # ???
                    
                    ray_start = (dino.rect.centerx, dino.rect.centery)
                    
                    # Se acertou algo, distancia vai apenas até o objeto
                    if ray['hit']:
                        angle = math.radians(settings.RAYS[i])
                        ray_end = (
                            int(ray_start[0] + ray['distance'] * math.cos(angle)),
                            int(ray_start[1] + ray['distance'] * math.sin(angle))
                        )
                    else:
                        angle = math.radians(settings.RAYS[i])
                        ray_end = (
                            int(ray_start[0] + settings.RAY_LENGTH * math.cos(angle)),
                            int(ray_start[1] + settings.RAY_LENGTH * math.sin(angle))
                        )
                    
                    pygame.draw.line(self.screen, ray_color, ray_start, ray_end, 2)

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
        self.last_spawn = pygame.time.get_ticks()

        for dino in self.dinos:
            dino.reset()

        self.active_dino_count = self.population_size

        for obstacle in self.obstacles:
            obstacle.kill()
        self.obstacles.empty()

        Obstacle.GLOBAL_SPEED = settings.OBSTACLE_SPEED

    def run(self):
        self.running = True
        self.reset_game()
        Obstacle.GLOBAL_SPEED = settings.OBSTACLE_SPEED
        while self.running:     
            self.handle_input()
            self.update_game_state() 
            self.draw_game()        
            
            self.clock.tick(settings.FPS)     
        
        return self.score 
    

if __name__ == '__main__':
    pygame.init()
    
    test_screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))

    game_instance = Training(screen=test_screen)
    
    game_instance.run()

    pygame.quit()
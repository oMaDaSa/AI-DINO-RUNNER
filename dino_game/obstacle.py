import pygame
from . import settings
import random

class Obstacle(pygame.sprite.Sprite):
    GLOBAL_SPEED = settings.OBSTACLE_SPEED

    def __init__(self, width:int = settings.OBSTACLE_WIDTH, height:int=settings.OBSTACLE_HEIGHT, speed:float = settings.OBSTACLE_SPEED):
        super().__init__()

        #APARENCIA 
        self.image = pygame.Surface([width, height])
        self.image.fill(settings.OBSTACLE_GREEN)

        #POSICAO
        self.rect = self.image.get_rect()
        self.rect.x = settings.SCREEN_WIDTH + random.randint(50, 200) # Spawn fora da tela, com uma variação
        self.rect.bottom = settings.GROUND_LEVEL

        #MOVIMENTACAO
        self.speed = speed
        
    def update(self):
        self.rect.x += Obstacle.GLOBAL_SPEED

        #destroi se sair da tela
        if self.rect.right < 0 :
            self.kill
    
    def draw(self, surface:pygame.Surface):
        surface.blit(self.image, self.rect)

    def reset(self):
        self.rect.x = settings.SCREEN_WIDTH + random.randint(50, 200)
        self.rect.bottom = settings.GROUND_LEVEL

if __name__ == '__main__':
    pygame.init()

    screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
    
    obstacles =  pygame.sprite.Group()
    obstacle = Obstacle()
    obstacles.add(obstacle)

    clock = pygame.time.Clock()
    running = True
    spawn_timer = 0

    Obstacle.GLOBAL_SPEED = settings.OBSTACLE_SPEED

    last_spawn = 0

    while running:
        Obstacle.GLOBAL_SPEED -= settings.SPEED_INCREASE
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        current_time = pygame.time.get_ticks()

        #reduz intervalo de spawn com o tempo, para compensar aumento de velocidade
        spawn_interval = max(300, settings.SPAWN_INTERVAL + Obstacle.GLOBAL_SPEED)

        if current_time - last_spawn >= spawn_interval:
            new_obstacle = Obstacle()
            obstacles.add(new_obstacle)
            last_spawn = current_time

        obstacles.update()
        #desenha ceu
        screen.fill(settings.SKY_BLUE)

        #desenha chao
        pygame.draw.rect(screen, settings.GROUND_BROWN, pygame.Rect(0, settings.GROUND_LEVEL, settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT - settings.GROUND_LEVEL))

        #desenha todos os obstaculos
        for sprite in obstacles:
            screen.blit(sprite.image, sprite.rect)

        pygame.display.flip()
        clock.tick(settings.FPS)

    pygame.quit()


        

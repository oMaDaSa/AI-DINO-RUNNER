import pygame
import settings
import random

class Obstacle(pygame.sprite.Sprite):
    GLOBAL_SPEED = settings.OBSTACLE_SPEED

    def __init__(self, is_flying=False, speed:float = settings.OBSTACLE_SPEED):
        super().__init__()

        self.is_flying = is_flying
        self.is_double = False

        if is_flying:
            if random.randint(0, 1) == 1:
                self.is_double = True
            self.width = settings.FLYING_OBSTACLE_WIDTH
            self.height = settings.FLYING_OBSTACLE_HEIGHT
        else:
            self.width = settings.OBSTACLE_WIDTH
            self.height = settings.OBSTACLE_HEIGHT

        #APARENCIA 
        self.image = pygame.Surface([self.width, self.height])
        
        if is_flying:
            self.image.fill(settings.COLOR_FLYING_OBSTACLE)
        else:
            self.image.fill(settings.COLOR_GROUND_OBSTACLE)

        #POSICAO
        rand = random.randint(50, 200)
        self.rect = self.image.get_rect()
        self.rect.x = settings.SCREEN_WIDTH + rand # Spawn fora da tela, com uma variação
        if is_flying:
            self.altitude = random.choice(settings.FLYING_OBSTACLE_ALTITUDE)
        else:
            self.altitude = 0

        self.rect.bottom = settings.GROUND_LEVEL - self.altitude

        if self.is_double: 
            self.image2 = pygame.Surface([self.width, self.height])
            self.image2.fill(settings.COLOR_FLYING_OBSTACLE)
            self.rect2 = self.image2.get_rect()
            self.rect2.x = settings.SCREEN_WIDTH + rand + 20
            self.rect2.bottom = settings.GROUND_LEVEL - (self.altitude+60) 

        #MOVIMENTACAO
        self.speed = speed
        
    def update(self):
        self.rect.x += Obstacle.GLOBAL_SPEED
        if self.is_double:
            self.rect2.x += Obstacle.GLOBAL_SPEED

        #destroi se sair da tela
        if self.rect.right < 0 :
            self.kill()
    
    def draw(self, surface:pygame.Surface):
        surface.blit(self.image, self.rect)
        if self.is_double:
            surface.blit(self.image2, (self.rect2.x, self.rect2.y))

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
            is_flying = random.randint(0,1)
            new_obstacle = Obstacle(is_flying = is_flying)
            obstacles.add(new_obstacle)
            last_spawn = current_time

        obstacles.update()
        #desenha ceu
        screen.fill(settings.COLOR_SKY)

        #desenha chao
        pygame.draw.rect(screen, settings.COLOR_GROUND, pygame.Rect(0, settings.GROUND_LEVEL, settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT - settings.GROUND_LEVEL))

        #desenha todos os obstaculos
        for sprite in obstacles:
            screen.blit(sprite.image, sprite.rect)

        pygame.display.flip()
        clock.tick(settings.FPS)

    pygame.quit()


        

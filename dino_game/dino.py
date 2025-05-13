import pygame
import settings

class Dino(pygame.sprite.Sprite):

    def __init__(self, x:int, y:int, width:int=settings.DINO_WIDTH, height:int=settings.DINO_HEIGHT):
        super().__init__()

        #APARENCIA 
        self.image = pygame.Surface([width, height])
        self.image.fill(settings.DINO_PURPLE)

        #POSICAO
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.rect.bottom = settings.GROUND_LEVEL #inicia no chao

        #MOVIMENTACAO
        self.velocity_y:float = 0
        self.is_jumping:bool = False
        self.on_ground:bool = True

        self._initial_x = x
        self._initial_y = settings.GROUND_LEVEL

        self.width = width
        self.height = height

    def jump(self):
        if self.on_ground:
            self.velocity_y = -settings.JUMP_FORCE
            self.is_jumping = True
            self.on_ground = False

    def update(self):
        if not self.on_ground:
            self.velocity_y += settings.GRAVITY
        
        self.rect.y += int(self.velocity_y) #move o dino com base em sua velocidade em y

        if self.rect.bottom >= settings.GROUND_LEVEL:
            self.rect.bottom = settings.GROUND_LEVEL
            self.velocity_y = 0
            self.is_jumping = False
            self.on_ground = True
        else:
            self.on_ground = False
            
    def draw(self, surface:pygame.Surface):
        surface.blit(self.image, self.rect)

    def reset(self):
        self.rect.x = self._initial_x
        self.rect.y = self._initial_y
        self.velocity_y = 0
        self.is_jumping = False
        self.on_ground = True


#testar colisao e pulo
if __name__ == '__main__':
    pygame.init()

    screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))

    dino = Dino(x=100, y=settings.GROUND_LEVEL)

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    dino.jump()

        dino.update()

        #preenche o ceu
        screen.fill(settings.SKY_BLUE) 
        
        #desenha chao
        pygame.draw.rect(screen, settings.GROUND_BROWN, pygame.Rect(0, settings.GROUND_LEVEL, settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT - settings.GROUND_LEVEL))


        dino.draw(screen)

        pygame.display.flip()
        clock.tick(settings.FPS) #FRAME RATE CAP

    pygame.quit() 
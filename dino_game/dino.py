import pygame
import settings

class Dino(pygame.sprite.Sprite):

    def __init__(self, x:int, y:int, width:int=settings.DINO_WIDTH, height:int=settings.DINO_HEIGHT):
        super().__init__()

        #APARENCIA 
        self.color = settings.DINO_PURPLE
        self.image = pygame.Surface([width, height])
        self.image.fill(self.color)
        self.height = settings.DINO_HEIGHT
        self.crouch_height = settings.DINO_CROUCH_HEIGHT
        self.width = width

        

        #POSICAO
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.rect.bottom = settings.GROUND_LEVEL #inicia no chao
        self.ground_y = y # Store original y position as ground level

        #MOVIMENTACAO
        self.velocity_y:float = 0
        self.is_jumping:bool = False
        self.on_ground:bool = True
        self.is_crouching = False

        self._initial_x = x
        self._initial_y = settings.GROUND_LEVEL


    def jump(self):
        if self.on_ground and not self.is_crouching:
            self.velocity_y = -settings.JUMP_FORCE
            self.is_jumping = True
            self.on_ground = False
            return True
        return False
    
    def crouch(self):
        if self.on_ground and not self.is_crouching and not self.is_jumping:
            self.is_crouching = True
            self.image = pygame.Surface([self.width, self.crouch_height])
            self.image.fill(self.color)
            # ajusta rect para manter a posição
            bottom = self.rect.bottom
            self.rect = self.image.get_rect()
            self.rect.x = self._initial_x
            self.rect.bottom = bottom
            return True
        return False

    def stand(self):
        if self.is_crouching:
            self.is_crouching = False
            self.image = pygame.Surface([self.width, self.height])
            self.image.fill(self.color)
            # ajusta rect para manter a posição
            bottom = self.rect.bottom
            self.rect = self.image.get_rect()
            self.rect.x = self._initial_x
            self.rect.bottom = bottom
            return True
        return False


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
        self.is_crouching = False


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
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    dino.jump()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    dino.crouch()
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_DOWN:
                    dino.stand()

        dino.update()

        #preenche o ceu
        screen.fill(settings.SKY_BLUE) 
        
        #desenha chao
        pygame.draw.rect(screen, settings.GROUND_BROWN, pygame.Rect(0, settings.GROUND_LEVEL, settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT - settings.GROUND_LEVEL))


        dino.draw(screen)

        pygame.display.flip()
        clock.tick(settings.FPS) #FRAME RATE CAP

    pygame.quit() 
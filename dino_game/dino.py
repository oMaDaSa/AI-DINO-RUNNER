import pygame
import settings
import math

class Dino(pygame.sprite.Sprite):

    def __init__(self, x:int, y:int, width:int=settings.DINO_WIDTH, height:int=settings.DINO_HEIGHT, alpha = 255, dino_id = 0):
        super().__init__()

        #APARENCIA 
        self.color = settings.DINO_PURPLE.copy()
        self.color.append(alpha) #adiciona transparencia
        self.image = pygame.Surface([width, height], pygame.SRCALPHA)
        self.image.fill(self.color)
        self.height = settings.DINO_HEIGHT
        self.crouch_height = settings.DINO_CROUCH_HEIGHT
        self.width = width

        #Para população
        self.is_alive = True
        self.id = dino_id
        self.fitness = 0 #quantos frames ele sobreviveu
        self.q_table = {} #cada dinossauro tem sua q_table
        self.last_state = None
        self.last_action = None

        #totais
        self.total_crouches = 0
        self.total_jumps = 0

        #Posição
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.rect.bottom = settings.GROUND_LEVEL #inicia no chao
        self.ground_y = y # Store original y position as ground level

        #Movimentação
        self.velocity_y:float = 0
        self.is_jumping:bool = False
        self.on_ground:bool = True
        self.is_crouching = False

        self._initial_x = x
        self._initial_y = settings.GROUND_LEVEL

        self.raycount = settings.RAYCOUNT
        self.rays = []
        self.init_rays()


    def init_rays(self):
        self.rays = []
        for _ in range(self.raycount):
            self.rays.append({
                'start': (0,0),
                'end': (0,0),
                'hit': False,
                'distance': float('inf'),
                'obstacle_type': None  #flying ou ground
            })
        
    def cast_rays(self, obstacles):
        self.init_rays()

        origin_x = self.rect.centerx
        origin_y = self.rect.centery
        
        origin_x = self.rect.centerx
        origin_y = self.rect.centery

        for i, angle in enumerate(settings.RAYS):
            angle_rad = math.radians(angle)
            #o tamanho máximo do ray
            end_x = origin_x + settings.RAY_LENGTH * math.cos(angle_rad)
            end_y = origin_y + settings.RAY_LENGTH * math.sin(angle_rad)

            closest_hit_dist = settings.RAY_LENGTH
            hit_type = None

            for obstacle in obstacles:
                clipped_segment_points = obstacle.rect.clipline(
                    (origin_x, origin_y),
                    (end_x, end_y)
                )
                if clipped_segment_points:
                    intersect_x, intersect_y = clipped_segment_points[0]
                    # Calcula a distancia entre a origem do raio e esse ponto de intersecção
                    dist_to_intersection = math.hypot(intersect_x - origin_x, intersect_y - origin_y)

                    if dist_to_intersection < closest_hit_dist:
                        closest_hit_dist = dist_to_intersection
                        hit_type = 'flying' if obstacle.is_flying else 'ground'
                
            if hit_type is not None: # Se um obstaculo foi atingido
                self.rays[i]['hit'] = True
                self.rays[i]['distance'] = closest_hit_dist
                self.rays[i]['obstacle_type'] = hit_type
                
        closest_ground = float('inf')
        closest_flying = float('inf')

        for ray in self.rays:
            if ray['hit']:
                if ray['obstacle_type'] == 'ground' and ray['distance'] < closest_ground:
                    closest_ground = ray['distance']
                elif ray['obstacle_type'] == 'flying' and ray['distance'] < closest_flying:
                    closest_flying = ray['distance']
        
        if closest_ground <= 0.0: closest_ground = 0.0
        if closest_flying <= 0.0: closest_flying = 0.0

        return {
            'ground_detected': closest_ground < float('inf'),
            'flying_detected': closest_flying < float('inf'),
            'ground_distance': closest_ground,
            'flying_distance': closest_flying
        }

    def jump(self):
        if self.on_ground and not self.is_crouching:
            self.velocity_y = -settings.JUMP_FORCE
            self.is_jumping = True
            self.on_ground = False
            self.total_jumps += 1
            return True
        return False
    
    def crouch(self):
        if self.on_ground and not self.is_crouching and not self.is_jumping:
            self.is_crouching = True
            self.image = pygame.Surface([self.width, self.crouch_height], pygame.SRCALPHA)
            self.image.fill(self.color)
            # ajusta rect para manter a posição
            bottom = self.rect.bottom
            self.rect = self.image.get_rect()
            self.rect.x = self._initial_x
            self.rect.bottom = bottom
            self.total_crouches += 1
            return True
        return False

    def stand(self):
        if self.is_crouching:
            self.is_crouching = False
            self.image = pygame.Surface([self.width, self.height], pygame.SRCALPHA)
            self.image.fill(self.color)
            # ajusta rect para manter a posição
            bottom = self.rect.bottom
            self.rect = self.image.get_rect()
            self.rect.x = self._initial_x
            self.rect.bottom = bottom
            return True
        return False


    def update(self):
        if self.is_alive:
            self.fitness += 1

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
        self.is_alive = True
        self.fitness = 0
        self.last_state = None
        self.last_state = None
        self.current_decision_state = None
        self.current_decision_action = None

    def die(self):
        self.is_alive = False

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
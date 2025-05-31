import pygame
import settings
from dino import Dino
from obstacle import Obstacle
from base_game import BaseAIGame
import random
import math
import numpy as np

class Train(BaseAIGame):
    def __init__(self, screen: pygame.Surface, custom_config=None):
        super().__init__(screen)
        self.last_spawn = pygame.time.get_ticks()
        self.custom_config = custom_config

        # Slider de velocidade
        self.speed_multiplier = 1.0
        self.slider_rect = pygame.Rect(10, 40, 100, 20)
        self.slider_handle_rect = pygame.Rect(60, 40, 10, 20)
        self.slider_dragging = False
        self.training_fps = settings.TRAININGFPS

        #População
        if custom_config: self.population_size = custom_config['POPULATION_SIZE']
        else: self.population_size = settings.POPULATION_SIZE

        self.dinos = pygame.sprite.Group()
        self.active_dino_count = 0
        self.best_dino = None
        self.best_fitness = 0

        #Q-values visualização
        self.q_val_no_action = 0.0
        self.q_val_jump = 0.0
        self.q_val_crouch = 0.0
        self.q_val_stand = 0.0

        #Detecção de obstáculos visualização
        self.obstacle_detection = {
            'ground_detected': False,
            'flying_detected': False,
            'ground_distance': float('inf'),
            'flying_distance': float('inf')
        }

        for i in range(self.population_size):
            alpha = 70 #semi transparente
            dino = Dino(x = 50, y = settings.GROUND_LEVEL + 60, alpha = alpha, dino_id = i)
            self.dinos.add(dino)
            self.sprites.add(dino)

        self.dino = list(self.dinos)[0]
        self.active_dino_count = self.population_size

        self.episodes_this_session = 0

    def detect_obstacles(self, dino):
        ground_obstacle_detected = False
        flying_obstacle_detected = False
        closest_ground_obstacle_distance = float('inf')
        closest_flying_obstacle_distance = float('inf')

        for i, ray in enumerate(dino.rays):
            if ray['hit']:

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
    
    def choose_action(self, state_tuple, dino=None):
        if dino is None:
            dino = self.dino

        #pegar a informação dos obstaculos ao redor
        obstacle_info = self.detect_obstacles(dino)

        self.obstacle_detection = obstacle_info 

        #pega os q_value pra esse estado
        #0 = nada/ 1 = pulo/ 2 = agachar/ 3 = levantar
        default_q_list = [0.0, 0.0, 0.0, 0.0]
        q_values = list(dino.q_table.get(state_tuple, default_q_list))


        self.q_val_no_action = q_values[0]
        self.q_val_jump = q_values[1]
        self.q_val_crouch = q_values[2]
        self.q_val_stand = q_values[3]  

        #exploração
        if random.uniform(0, 1) < self.epsilon:
            rand_val = random.choice([0,1,2,3])
            return rand_val

        # É possivel guiar o aprendizado, dando sugestões para uma fase inicial de treinamento (epsilon acima de um determinado valor)
        # Não forçar a escolha, mas sugerir ela
        return np.argmax(q_values)
                
            
    def select_best_dinosaur(self):
        best_fitness = 0
        best_dino = None

        for dino in self.dinos:
            if dino.fitness > best_fitness:
                best_fitness = dino.fitness
                best_dino = dino
            
        if best_dino is not None:
            self.best_dino = best_dino
            self.best_fitness = best_fitness
            if best_dino.q_table:
                self.q_table = best_dino.q_table.copy()

            print(f"Episódio {self.current_episode}: Melhor dinossauro: {best_dino.id} com fitness {best_fitness}")


    def update_game_state(self):

        if self.game_over:
            self.select_best_dinosaur()
            self.reset_game()

            self.current_episode += 1
            self.episodes_this_session += 1
            min_epsilon = self.custom_config.get('EPSILON_MIN', settings.EPSILON_MIN) if self.custom_config else settings.EPSILON_MIN
            decay_rate = self.custom_config.get('EPSILON_DECAY', settings.EPSILON_DECAY) if self.custom_config else settings.EPSILON_DECAY
            self.epsilon = max(min_epsilon, self.epsilon * decay_rate)

            if self.episodes_this_session > 0 and self.episodes_this_session % 50 == 0:
                self.save_q_table()
            return # Encerra esse game. A próxima chamada vai criar a nova geração

        #etapa 1: cada dinossauro vivo observa o estado do jogo
        for dino in self.dinos:
            if not dino.is_alive: #os mortos não fazem nada
                continue

            dino.cast_rays(self.obstacles)
            observed_state_s = self.get_state(dino) #estado s pra decisão

            action_to_take = self.choose_action(observed_state_s, dino) #escolhe ação pro estado

            cur_decision = observed_state_s # Usado para dino.last_state
            cur_action = action_to_take   # Usado para dino.last_action

            # faz ação
            self.perform_action(dino, action_to_take)
            
        #etapa 2: atualiza o mundo
        super().update_game_state()

        #fase 3: pra cada dinossauro, observar os resultado e aprender com os passos anteriores
        new_active_dino_count = 0
        default_q_list_terminal = [0.0, 0.0, 0.0, 0.0] # Para uso no update terminal
        for dino in self.dinos:
            if not dino.is_alive:
                continue
            
            # estado s' é o estado apos o sprite update
            dino.cast_rays(self.obstacles)
            state_s_prime = self.get_state(dino)

            speed_factor = min(1.0, abs(Obstacle.GLOBAL_SPEED) / 10)
            # reward = 0.1 + (0.05 * speed_factor) # Recompensa base por sobreviver
            current_reward = settings.BASE_SURVIVAL_REWARD + (settings.SPEED_FACTOR_REWARD * speed_factor)

            #verifica colisao e aplica custos
            collided_this_step = False
            hit_obstacles_sprites = self.check_collisions(dino)

            #se colidiu
            if hit_obstacles_sprites:
                current_reward = -settings.COLLISION_COST # Recompensa negativa por colisão
                collided_this_step = True
            else: #se nao colidiu
                if dino.last_action == 1: # Custo do Pulo
                    current_reward -= settings.JUMP_COST
                elif dino.last_action == 2: # Custo de Agachar
                    current_reward -= settings.CROUCH_COST

            # Atualiza o q-learning com (dino.last_state, dino.last_action) como (s, a)
            # state_s_prime é s', e current_reward_for_update é r.
            if dino.last_state is not None and dino.last_action is not None:
                if collided_this_step: # se colidiu (state_s_prime é terminal)
                    # terminal update: Q(s,a) = Q(s,a) + alpha * (r - Q(s,a))
                    # porque o max_future_q pra um estado terminal é 0
                    
                    current_q_values_list = list(dino.q_table.get(dino.last_state, default_q_list_terminal))
                    current_q_values = current_q_values_list[:]

                    old_q_value = current_q_values[dino.last_action]
                    alpha = self.custom_config.get('ALPHA', settings.ALPHA) if self.custom_config else settings.ALPHA
                    new_q_value = old_q_value + alpha * (current_reward - old_q_value)
                    current_q_values[dino.last_action] = new_q_value
                    dino.q_table[dino.last_state] = current_q_values
                    
                else: # state_s_prime não é terminal
                    alpha = self.custom_config.get('ALPHA', settings.ALPHA) if self.custom_config else settings.ALPHA
                    gamma = self.custom_config.get('GAMMA', settings.GAMMA) if self.custom_config else settings.GAMMA
                    default_q_list = [0.0, 0.0, 0.0, 0.0]

                    current_q_values_from_table = dino.q_table.get(dino.last_state, default_q_list)
                    current_q_values = list(current_q_values_from_table)
                    dino.q_table[dino.last_state] = current_q_values

                    old_q_value = current_q_values[dino.last_action]
                    
                    next_q_values_from_table = dino.q_table.get(state_s_prime, default_q_list)
                    next_q_values = list(next_q_values_from_table)
                    dino.q_table[state_s_prime] = next_q_values 
                    
                    max_future_q = np.max(next_q_values)
                    
                    new_q_value = old_q_value + alpha * (current_reward + gamma * max_future_q - old_q_value)
                    current_q_values[dino.last_action] = new_q_value
                    dino.q_table[dino.last_state] = current_q_values

            # Atualiza histórico do dinossauro
            if collided_this_step:
                dino.die()
                dino.last_state = None
                dino.last_action = None
            else:
                dino.last_state = cur_decision
                dino.last_action = cur_action
                new_active_dino_count += 1
        
        self.active_dino_count = new_active_dino_count
        if self.active_dino_count == 0:
            self.game_over = True
    
    def reset_game(self):
        super().reset_game()
        self.last_spawn = pygame.time.get_ticks()

        # Preparando a q-table base pros novos dinosssauros
        # Ela é uma cópia da self.q_table que deve armazenar a q-table do melhor dino anterior ou de um arquivo carregado
        base_q_table = {}
        if self.q_table: 
            # itera cada k e seus q-values
            for state_key, q_value_list in self.q_table.items():
                # e cria uma nova lista. necessário pois se usarmos .copy, as listas internas ainda apontarão para o mesmo objeto
                base_q_table[state_key] = list(q_value_list)
        
        # reseta cada dinossauro e cria uma cópia da tabela Q base para cada dinossauro
        for dino in self.dinos:
            dino.reset()

            new_dino_q_table = {}
            for state_key, q_value_list in base_q_table.items():
                new_dino_q_table[state_key] = list(q_value_list)

            dino.q_table = new_dino_q_table


        self.active_dino_count = self.population_size

    def draw_info(self):
        super().draw_info() #score
        
        small_font = pygame.font.Font(None, 20)

        # desenha o slider de velocidade
        pygame.draw.rect(self.screen, settings.COLOR_BUTTON, self.slider_rect)
        pygame.draw.rect(self.screen, settings.COLOR_TEXT, self.slider_handle_rect)
        speed_text = self.font.render(f"Speed: {self.speed_multiplier:.1f}x", True, settings.COLOR_TEXT)
        self.screen.blit(speed_text, (120, 40))

        #painel no lado direito
        info_panel = pygame.Rect(settings.SCREEN_WIDTH - 200, 10, 190, 380)
        info_surface = pygame.Surface((info_panel.width, info_panel.height), pygame.SRCALPHA) #superficie, draw rect nao suporta trasparência
        info_surface.fill((0, 0, 0, 180))  # preto com transparencia
        self.screen.blit(info_surface, info_panel)
        pygame.draw.rect(self.screen, (200, 200, 200), info_panel, 1) #borda

        y_pos = info_panel.y + 10
        line_height = 20

        #titulo
        title_text = small_font.render("Training info", True, settings.COLOR_TEXT)
        self.screen.blit(title_text, (info_panel.x + 5, y_pos))
        y_pos += line_height + 5

        stats = [
            f"Episode: {self.current_episode}",
            f"Population: {self.active_dino_count}/{self.population_size}",
            f"Epsilon: {self.epsilon:.3f}", 
            f"Best Fitness: {self.best_fitness:.1f}"  
        ]

        for stat in stats:
            stat_text = small_font.render(stat, True, settings.COLOR_TEXT)
            self.screen.blit(stat_text, (info_panel.x + 5, y_pos))
            y_pos += line_height
        

        #Seção dos q-values (primeiro dino apenas)
        y_pos += 5 #pequeno espaçamento adicional
        q_title = small_font.render("Q-values: ", True,settings.COLOR_TEXT)
        self.screen.blit(q_title, (info_panel.x + 5, y_pos))
        y_pos += line_height

        q_values = [self.q_val_no_action, self.q_val_jump, self.q_val_crouch, self.q_val_stand]
        q_labels = ["None", "Jump", "Crouch", "Stand"]
        
        max_q_index = np.argmax(q_values) #para destacar o maior deles

        bar_max_width = 120
        bar_height = 12
        
        # maior q pra escala das barras
        max_q = max(abs(max(q_values)), abs(min(q_values)), 0.1) #0.1 para evitar divisão por 0

        for i, (q_val, label) in enumerate(zip(q_values, q_labels)):
            #label
            text_color = (255, 255, 0) if i == max_q_index else settings.COLOR_TEXT
            q_text = small_font.render(f"{label}: {q_val:.2f}", True, text_color)
            self.screen.blit(q_text, (info_panel.x + 5, y_pos))

            # barra
            bar_width = abs(q_val) / max_q * bar_max_width
            bar_color = (0, 255, 0) if q_val >= 0 else (255, 0, 0)
            bar_x = info_panel.x + 5
            bar_y = y_pos + line_height - 2
            #borda
            pygame.draw.rect(self.screen, (150, 150, 150), (bar_x, bar_y, bar_max_width, bar_height), 1)

            # preenche barra
            if q_val >= 0:
                pygame.draw.rect(self.screen, bar_color, (bar_x, bar_y, bar_width, bar_height))
            else:
                # For negative values, align to the left
                pygame.draw.rect(self.screen, bar_color, (bar_x, bar_y, bar_width, bar_height))
            
            y_pos += line_height + bar_height + 2  # espaço extra para as barras

        #seção de detecção de obstaculo
        y_pos += 5 
        #titulo
        obs_title = small_font.render("Obstacles:", True, settings.COLOR_TEXT)
        self.screen.blit(obs_title, (info_panel.x + 5, y_pos))
        y_pos += line_height
        
        # obstaculo terrestre
        ground_dist = str(round(self.obstacle_detection['ground_distance'])) if self.obstacle_detection['ground_distance'] != float('inf') else "-"
        ground_text = small_font.render(f"Ground: {ground_dist}", True, settings.COLOR_GROUND_OBSTACLE if self.obstacle_detection['ground_detected'] else settings.COLOR_TEXT)
        self.screen.blit(ground_text, (info_panel.x + 5, y_pos))
        y_pos += line_height
        
        # obstaculo voador
        flying_dist = str(round(self.obstacle_detection['flying_distance'])) if self.obstacle_detection['flying_distance'] != float('inf') else "-"
        flying_text = small_font.render(f"Flying: {flying_dist}", True, settings.COLOR_FLYING_OBSTACLE if self.obstacle_detection['flying_detected'] else settings.COLOR_TEXT)
        self.screen.blit(flying_text, (info_panel.x + 5, y_pos))

    def draw_game(self):
        self.screen.fill(settings.COLOR_SKY)
        pygame.draw.rect(self.screen, settings.COLOR_GROUND, pygame.Rect(0, settings.GROUND_LEVEL, settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT - settings.GROUND_LEVEL))
        
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

        self.draw_info()

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.slider_rect.collidepoint(event.pos):
                    self.slider_dragging = True
            elif event.type == pygame.MOUSEBUTTONUP:
                self.slider_dragging = False
            elif event.type == pygame.MOUSEMOTION and self.slider_dragging:
                mouse_x = event.pos[0]
                slider_x = max(self.slider_rect.left, min(mouse_x, self.slider_rect.right))
                self.slider_handle_rect.centerx = slider_x
                ratio = (slider_x - self.slider_rect.left) / self.slider_rect.width
                self.speed_multiplier = 0.1 + ratio * 19.9
                self.training_fps = int(settings.TRAININGFPS * self.speed_multiplier)

    def run(self):
        self.running = True

        if self.game_over: # Se está começando de um game over
             self.reset_game()

        while self.running:     
            self.handle_input()
            if not self.running: 
                break
            self.update_game_state() 
            self.draw_game()        
            pygame.display.flip()
            self.clock.tick(self.training_fps)

        self.save_q_table()     
        
        return self.score 

if __name__ == '__main__':
    pygame.init()
    
    test_screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)

    game_instance = Train(screen=test_screen)
    
    game_instance.run()

    pygame.quit()
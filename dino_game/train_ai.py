import pygame
import settings
from dino import Dino
from obstacle import Obstacle
import random
import math
import numpy as np
import os
import json

class Train:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.last_spawn = pygame.time.get_ticks()

        self.running = False
        self.game_over = False
        self.score = 0
        
        #População
        self.population_size = settings.POPULATION_SIZE
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

        self.sprites = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()

        for i in range(self.population_size):
            alpha = 50 #semi transparente
            dino = Dino(x = 50, y = settings.GROUND_LEVEL + 60, alpha = alpha, dino_id = i)
            self.dinos.add(dino)
            self.sprites.add(dino)

        self.dino = list(self.dinos)[0]
        self.active_dino_count = self.population_size
        self.obstacle_spawn_timer = 0

        self.q_table = {}
        self.epsilon = settings.EPSILON_INIT
        self.current_episode = 0
        self.episodes_this_session = 0
        self.q_table_file = "dino_q_table.json"
        self.load_q_table()
        self.distance_bin_edges = np.linspace(0, settings.RAY_LENGTH, settings.DISTANCE_BINS + 1)

    def discretize_value(self, value, bin_edges):
        idx = np.digitize(value, bin_edges[1:-1])
        return idx

    def get_state(self, dino=None):
        if dino is None:
            dino = self.dino
        
        state_components = []
        for ray in  dino.rays:
            dist = max(0, ray['distance'])
            distance_bin = self.discretize_value(dist, self.distance_bin_edges)
            state_components.append(distance_bin)

            # (0: nenhum obstaculo, 1: obstaculo terreste, 2: obstaculo voador)
            if not ray['hit']:
                obstacle_type_value = 0
            elif ray['obstacle_type'] == 'ground':
                obstacle_type_value = 1
            elif ray['obstacle_type'] == 'flying':
                obstacle_type_value = 2
            else:
                obstacle_type_value = 0  # Default
            
            state_components.append(obstacle_type_value)

        dino_vy_bin = self.discretize_value(dino.velocity_y, settings.VELOCITY_BINS)
        game_speed_bin = self.discretize_value(Obstacle.GLOBAL_SPEED, settings.GAME_SPEED_BINS)
        
        state_components.extend([dino_vy_bin, game_speed_bin])

        return tuple(state_components)
    

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
        q_values = list(self.q_table.get(state_tuple, default_q_list))


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

    def spawn_obstacle(self):
        is_flying = random.randint(0,1)
        obstacle = Obstacle(is_flying = is_flying)
        self.sprites.add(obstacle)
        self.obstacles.add(obstacle)
    
    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    return
                
            
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
            self.epsilon = max(settings.EPSILON_MIN, self.epsilon * settings.EPSILON_DECAY)

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
            if action_to_take == 1: # Pular
                dino.jump()
            elif action_to_take == 2: # Agachar 
                dino.crouch()
            elif action_to_take == 3: # Levantar (nova ação)
                if dino.is_crouching: # Só levanta se estiver agachado
                    dino.stand()
            
        #etapa 2: atualiza o mundo
        self.sprites.update() 
        
        Obstacle.GLOBAL_SPEED -= settings.SPEED_INCREASE #fica mais rapido
        self.score += 1 #/ settings.TRAININGFPS #incrementa score

        # spawn de obstaculos
        self.obstacle_spawn_timer += 1
        calculated_interval = settings.SPAWN_INTERVAL + (Obstacle.GLOBAL_SPEED * settings.SPAWN_INTERVAL_SPEED_EFFECT)
        spawn_interval = int(calculated_interval)
        
        if self.obstacle_spawn_timer >= spawn_interval:
            self.spawn_obstacle()
            self.obstacle_spawn_timer = 0

        #fase 3: pra cada dinossauro, observar os resultado e aprender com os passos anteriores
        new_active_dino_count = 0
        default_q_list_terminal = [0.0, 0.0, 0.0, 0.0] # Para uso no update terminal
        for dino in self.dinos:
            if not dino.is_alive:
                continue
            
            #stado s' é o estado apos o sprite update
            dino.cast_rays(self.obstacles)
            state_s_prime = self.get_state(dino)

            speed_factor = min(1.0, abs(Obstacle.GLOBAL_SPEED) / 10)
            # reward = 0.05 + (0.05 * speed_factor) # Recompensa base por sobreviver
            current_reward = 0.05 + (0.05 * speed_factor) # Renomeado para evitar confusão com 'reward_r'


            #verifica colisao e aplcia custos
            collided_this_step = False
            hit_obstacles_sprites = pygame.sprite.spritecollide(dino, self.obstacles, False, pygame.sprite.collide_rect)

            #se colidiu
            if hit_obstacles_sprites:
                actual_reward_for_update = -settings.COLLISION_COST # Recompensa negativa por colisão
                collided_this_step = True
            else: #se nao colidiu
                actual_reward_for_update = current_reward # Usa a recompensa base por sobreviver
                if dino.last_action == 1: # Custo do Pulo
                    actual_reward_for_update -= settings.JUMP_COST
                elif dino.last_action == 2: # Custo de Agachar (Ação 2)
                    actual_reward_for_update -= settings.CROUCH_COST
                # Nenhum custo específico para Ação 0 (Manter) ou Ação 3 (Levantar) aqui.

            # Atualiza o q-learning com (dino.last_state, dino.last_action) como (s, a)
            # state_s_prime é s', e actual_reward_for_update é r.
            if dino.last_state is not None and dino.last_action is not None:
                if collided_this_step: # se colidiu (state_s_prime é terminal)
                    # terminal update: Q(s,a) = Q(s,a) + alpha * (r - Q(s,a))
                    # porque o max_future_q pra um estado terminal é 0
                    
                    current_q_values_list = list(self.q_table.get(dino.last_state, default_q_list_terminal))
                    if len(current_q_values_list) < 4: # Garante 4 elementos
                        current_q_values_list.extend([0.0] * (4 - len(current_q_values_list)))
                    current_q_values = current_q_values_list[:] # Cópia mutável

                    if 0 <= dino.last_action < len(current_q_values): # Checagem de segurança
                        old_q_value = current_q_values[dino.last_action]
                        new_q_value = old_q_value + settings.ALPHA * (actual_reward_for_update - old_q_value)
                        current_q_values[dino.last_action] = new_q_value
                        self.q_table[dino.last_state] = current_q_values
                    else:
                        print(f"AVISO: dino.last_action ({dino.last_action}) fora do range para Q-values no estado terminal.")
                    
                else: # state_s_prime não é terminal
                    self.update_q_table(dino.last_state, dino.last_action, actual_reward_for_update, state_s_prime)

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

        score_text = self.font.render(f"Score: {int(self.score)}", True, settings.COLOR_TEXT)
        self.screen.blit(score_text, (10, 10))


    def reset_game(self):
        self.score = 0
        self.game_over = False
        self.obstacle_spawn_timer = 0
        self.last_spawn = pygame.time.get_ticks()

        #reseta dinossauros
        for dino in self.dinos:
            dino.reset()

        self.active_dino_count = self.population_size

        #clear obstacles
        for obstacle in self.obstacles:
            obstacle.kill()
        self.obstacles.empty()

        Obstacle.GLOBAL_SPEED = settings.OBSTACLE_SPEED

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
            self.clock.tick(settings.TRAININGFPS)

        self.save_q_table()     
        
        return self.score 
    
    def update_q_table(self, state, action, reward, next_state):
        default_q_list = [0.0, 0.0, 0.0, 0.0]

        current_q_values_from_table = self.q_table.get(state, default_q_list)
        current_q_values = list(current_q_values_from_table) # Cria cópia para modificação

        self.q_table[state] = current_q_values

        old_q_value = current_q_values[action]
        
        next_q_values_from_table = self.q_table.get(next_state, default_q_list)
        next_q_values = list(next_q_values_from_table) # Cria cópia
        self.q_table[next_state] = next_q_values 
        
        # Calcula o maximo futuro q_value
        max_future_q = np.max(next_q_values)
        
        #Atualiza o Q-value usando a formula Q-learning
        new_q_value = old_q_value + settings.ALPHA * (reward + settings.GAMMA * max_future_q - old_q_value)
        current_q_values[action] = new_q_value
        self.q_table[state] = current_q_values 

    def save_q_table(self):
        try:
            q_table_str_keys = {}
            for k, v in self.q_table.items():
                # Converte cada elemento na tuple key pra um int
                key_as_int = tuple(int(x) for x in k)
                q_table_str_keys[str(key_as_int)] = v # v será uma lista de 4 floats
                
            data = {
                "q_table": q_table_str_keys,
                "epsilon": float(self.epsilon),
                "total_episodes_trained": int(self.current_episode)
            }

            with open(self.q_table_file, 'w') as f:
                json.dump(data, f, indent=4) #indent para melhor leitura do JSON
            print(f"Q-table salvo em {self.q_table_file}")
        except Exception as e:
            print(f"Erro ao salvar a Q-Table: {e}")

    def load_q_table(self):
        if os.path.exists(self.q_table_file):
            try:
                with open(self.q_table_file, 'r') as f:
                    data = json.load(f)
                    loaded_q_table_str_keys = data.get("q_table", {})
                    self.q_table = {}
                    for k_str, v_list in loaded_q_table_str_keys.items():
                        # v_list são os Q-values (lista de floats)
                        try:
                            # Processamento da chave k_str
                            if 'np.int64' in k_str:
                                # numpy int
                                nums = []
                                for part in k_str.strip('()').split(','):
                                    part = part.strip()
                                    if 'np.int64' in part:
                                        num_str = part.split('(')[1].split(')')[0]
                                        nums.append(int(num_str))
                                    else:
                                        nums.append(int(part))
                                state_parts = tuple(nums)
                            else:
                                # python Int
                                state_parts = tuple(map(int, k_str.strip('()').split(',')))
                            
                            final_v_list = list(v_list)

                            self.q_table[state_parts] = final_v_list

                        except Exception as e:
                            print(f"Erro em Q-table key: {k_str} ou valor: {v_list} ({e})")
                                
                self.epsilon = data.get("epsilon", settings.EPSILON_INIT)
                self.current_episode = data.get("total_episodes_trained", 0) 
                print(f"Q-table carregada.")
            except Exception as e:
                print(f"Erro ao carregar Q-table: {e}. Criando uma nova.")
                self.q_table = {}
                self.epsilon = settings.EPSILON_INIT
                self.current_episode = 0
        else:
            print("Nenhuma Q-table encontrada. Iniciando uma nova")
            self.q_table = {} 
            self.epsilon = settings.EPSILON_INIT
            self.current_episode = 0
    

if __name__ == '__main__':
    pygame.init()
    
    test_screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))

    game_instance = Train(screen=test_screen)
    
    game_instance.run()

    pygame.quit()
import pygame
import settings
from dino import Dino
from obstacle import Obstacle
import random
import numpy as np
import os
import json

class BaseGame:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        self.running = False
        self.game_over = False
        self.score = 0
        
        self.sprites = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()
        self.obstacle_spawn_timer = 0

    def spawn_obstacle(self):
        is_flying = random.randint(0,1)
        obstacle = Obstacle(is_flying=is_flying)
        self.sprites.add(obstacle)
        self.obstacles.add(obstacle)
    
    def handle_input(self):
        pass

    def update_game_state(self):
        if self.game_over:
            return

        self.sprites.update()
        Obstacle.GLOBAL_SPEED -= settings.SPEED_INCREASE
        self.score += 1

        # Spawn de obstaculos
        self.obstacle_spawn_timer += 1
        calculated_interval = settings.SPAWN_INTERVAL + (Obstacle.GLOBAL_SPEED * settings.SPAWN_INTERVAL_SPEED_EFFECT)
        spawn_interval = int(calculated_interval)
        
        if self.obstacle_spawn_timer >= spawn_interval:
            self.spawn_obstacle()
            self.obstacle_spawn_timer = 0

    def draw_info(self):
        #score
        score_text = self.font.render(f"Score: {int(self.score)}", True, settings.COLOR_TEXT)
        self.screen.blit(score_text, (10, 10))

    def draw_game(self):
        self.draw_info()
        self.screen.fill(settings.COLOR_SKY)
        pygame.draw.rect(self.screen, settings.COLOR_GROUND, pygame.Rect(0, settings.GROUND_LEVEL, settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT - settings.GROUND_LEVEL))
        
        for entity in self.sprites:
            entity.draw(self.screen)

        score_text = self.font.render(f"Score: {int(self.score)}", True, settings.COLOR_TEXT)
        self.screen.blit(score_text, (10, 10))

        if self.game_over:    
            self.draw_game_over()
    
    def draw_game_over(self):
        overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128)) 
        self.screen.blit(overlay, (0,0))

        game_over_text = self.font.render("Game Over", True, (255,255,255))
        text_rect = game_over_text.get_rect(center=(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2 - 30))
        self.screen.blit(game_over_text, text_rect)
        
        final_score_text = self.small_font.render(f"Final Score: {int(self.score)}", True, (255,255,255))
        score_rect = final_score_text.get_rect(center=(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2 + 10))
        self.screen.blit(final_score_text, score_rect)
        restart_text = self.small_font.render("'R' - Restart | ESC - Menu", True, (200,200,200))
        restart_rect = restart_text.get_rect(center=(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2 + 50))
        self.screen.blit(restart_text, restart_rect)

        
    def check_collisions(self, dino):
        hit_obstacles = pygame.sprite.spritecollide(dino, self.obstacles, False, pygame.sprite.collide_rect)
        return hit_obstacles

    def reset_game(self):
        self.score = 0
        self.obstacle_spawn_timer = 0
        self.game_over = False
        
        for obstacle in self.obstacles:
            obstacle.kill()
        self.obstacles.empty()

        Obstacle.GLOBAL_SPEED = settings.OBSTACLE_SPEED # Reseta velocidade global

    def run(self):
        self.running = True
        self.reset_game() 
        
        while self.running:
            self.handle_input()
            self.update_game_state()
            self.draw_game()
            pygame.display.flip()
            
            self.clock.tick(settings.FPS)

        return self.score

class BaseAIGame(BaseGame):
    def __init__(self, screen: pygame.Surface, custom_config=None):
        super().__init__(screen)
        self.q_table = {}
        self.q_table_file = "dino_q_table.json"
        self.distance_bin_edges = np.linspace(0, settings.RAY_LENGTH, settings.DISTANCE_BINS + 1)

        # inicializar parametros
        self.epsilon = settings.EPSILON_INIT
        self.alpha = settings.ALPHA
        self.gamma = settings.GAMMA
        self.epsilon_decay = settings.EPSILON_DECAY
        self.epsilon_min = settings.EPSILON_MIN

        self.current_episode = 0
        self.load_q_table()

        if custom_config:
            if 'ALPHA' in custom_config:
                self.alpha = custom_config['ALPHA']
            if 'GAMMA' in custom_config:
                self.gamma = custom_config['GAMMA']
            if 'EPSILON_INIT' in custom_config:
                self.epsilon = custom_config['EPSILON_INIT']
            if 'EPSILON_DECAY' in custom_config:
                self.epsilon_decay = custom_config['EPSILON_DECAY']
            if 'EPSILON_MIN' in custom_config:
                self.epsilon_min = custom_config['EPSILON_MIN']
            if 'POPULATION_SIZE' in custom_config:
                self.population_size = custom_config['POPULATION_SIZE']


    def discretize_value(self, value, bin_edges):
        idx = np.digitize(value, bin_edges[1:-1])
        return idx

    def get_state(self, dino):
        state_components = []

        for ray in dino.rays:
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

    def choose_action(self, state_tuple):
        q_values = self.q_table.get(state_tuple, [0.0, 0.0, 0.0, 0.0])
        return np.argmax(q_values)
    
    def perform_action(self, dino, action):
        # executa a ação escolhida
        if action == 1: 
            if dino.is_crouching: 
                dino.stand()
            dino.jump()
        elif action == 2:
            dino.crouch()
        elif action == 3: 
            if dino.is_crouching: 
                dino.stand()
        # ação 0 é não fazer nada
    
    def handle_input(self): 
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                if self.game_over:
                    if event.key == pygame.K_r:
                        self.reset_game()
                        self.game_over = False 

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

                #CARREGA PARAMETROs
                self.epsilon = data.get("epsilon", settings.EPSILON_INIT)
                self.current_episode = data.get("total_episodes_trained", 0)
                training_params = data.get("training_params", {})
                self.alpha = training_params.get("alpha", settings.ALPHA)
                self.gamma = training_params.get("gamma", settings.GAMMA)
                self.epsilon_decay = training_params.get("epsilon_decay", settings.EPSILON_DECAY)
                self.epsilon_min = training_params.get("epsilon_min", settings.EPSILON_MIN)
                self.population_size = training_params.get("population_size", settings.POPULATION_SIZE)
                                
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
                "total_episodes_trained": int(self.current_episode),
                #parametros de trino
                "training_params": {
                    "alpha": float(self.alpha),
                    "gamma": float(self.gamma),
                    "epsilon_decay": float(self.epsilon_decay),
                    "epsilon_min": float(self.epsilon_min),
                    "population_size": int(getattr(self, 'population_size', settings.POPULATION_SIZE))
                }
            }

            with open(self.q_table_file, 'w') as f:
                json.dump(data, f, indent=4) #indent para melhor leitura do JSON
            print(f"Q-table salvo em {self.q_table_file}")
        except Exception as e:
            print(f"Erro ao salvar a Q-Table: {e}")

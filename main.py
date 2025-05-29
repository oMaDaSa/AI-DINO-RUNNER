import pygame
import sys
import os
import json

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'dino_game')))

import dino_game.settings as settings
import dino_game.game as game
import dino_game.train_ai as train_ai
import dino_game.watch_ai as watch_ai
import dino_game.versus as versus
import ui.training_config as training_config
import ui.menu as menu

class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))

        self.main_menu = menu.MainMenu(self.screen)
        self.current_game_instance = None
        self.running = True

    def play(self, gamemode):
        if gamemode == "play":
            self.current_game_instance = game.Game(self.screen)
        elif gamemode == "train":
            # Checa se qtable ja existe
            q_table_file = "dino_q_table.json"
            if not os.path.exists(q_table_file):
                # Tela de configuração se nao existir
                config_screen = training_config.TrainingConfig(self.screen)
                config = config_screen.run()
                
                #sai se cancelar
                if config is None:
                    return
            else:
                # se existe, lê a configuração existente
                with open(q_table_file, 'r') as f:
                    data = json.load(f)
                    # Extrai os parâmetros
                    training_params = data.get("training_params", {})
                    config = {}
                    config['ALPHA'] = training_params.get("alpha", settings.ALPHA)
                    config['GAMMA'] = training_params.get("gamma", settings.GAMMA)
                    config['EPSILON_INIT'] = data.get("epsilon", settings.EPSILON_INIT)
                    config['EPSILON_DECAY'] = training_params.get("epsilon_decay", settings.EPSILON_DECAY)
                    config['EPSILON_MIN'] = training_params.get("epsilon_min", settings.EPSILON_MIN)
                    config['POPULATION_SIZE'] = training_params.get("population_size", settings.POPULATION_SIZE)

            self.current_game_instance = train_ai.Train(self.screen, config)
        elif gamemode == "watch":
            self.current_game_instance = watch_ai.Watch(self.screen)
        elif gamemode == "versus":
            self.current_game_instance = versus.Versus(self.screen)
        score = self.current_game_instance.run()
        self.current_game_instance = None

    def quit_game(self):
        self.running = False

    def run(self):
        while self.running:
            selected_action_key = self.main_menu.run()

            if selected_action_key == "quit":
                self.quit_game()
            elif selected_action_key in ["play", "train", "watch", "versus"] :
                self.play(gamemode = selected_action_key)
            else:
                pass 

        pygame.quit()

if __name__ == '__main__':
    app = App()
    app.run()

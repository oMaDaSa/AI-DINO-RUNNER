import pygame
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'dino_game')))

import dino_game.settings as settings
import dino_game.game as game
import dino_game.train_ai as train_ai
import dino_game.watch_ai as watch_ai
import dino_game.versus as versus
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
            self.current_game_instance = train_ai.Train(self.screen)
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

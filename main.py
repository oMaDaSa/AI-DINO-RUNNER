import pygame

import sys, os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import dino_game.settings as settings
import dino_game.game as game
import ui.menu as menu

class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))

        self.main_menu = menu.MainMenu(self.screen)
        self.current_game_instance = None
        self.running = True

    def play(self):
        self.current_game_instance = game.Game(self.screen)
        score = self.current_game_instance.run()
        self.current_game_instance = None

    def quit_game(self):
        self.running = False

    def run(self):
        while self.running:
            selected_action_key = self.main_menu.run()

            if selected_action_key == "quit":
                self.quit_game()
            elif selected_action_key == "play":
                self.play()
            else:
                pass 

        pygame.quit()

if __name__ == '__main__':
    app = App()
    app.run()

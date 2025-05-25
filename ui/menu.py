import pygame
import sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import dino_game.settings as settings

class Button:
    def __init__(self, text, x, y, width, height, color, hover_color, font, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.font = font
        self.action = action
        self.is_hovered = False

    def draw(self, surface: pygame.Surface):
        current_color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, current_color, self.rect, border_radius = 10)

        text_surface = self.font.render(self.text, True, settings.TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def handle_event(self, event:pygame.event.Event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                if self.action:
                    self.action()
                return True
        return False
    
class MainMenu:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font_large = pygame.font.Font(None, 75) 
        self.font_medium = pygame.font.Font(None, 50) 
        self.font_small = pygame.font.Font(None, 30) 

        self.running = True
        self.selected_option = None

        btn_width = 300
        btn_height = 60
        btn_spacing = 20
        start_y = settings.SCREEN_HEIGHT // 2 - (3 * btn_height + 2 * btn_spacing) // 2

        self.buttons = [
            Button("Play", settings.SCREEN_WIDTH // 2 - btn_width // 2, start_y + 0 * (btn_height + btn_spacing), btn_width, btn_height, settings.BUTTON_GRAY, (180, 180, 180), self.font_medium, lambda: self.select_option("play")),

            Button("Train Model", settings.SCREEN_WIDTH // 2 - btn_width // 2, start_y + 1 * (btn_height + btn_spacing), btn_width, btn_height, settings.BUTTON_GRAY, (180, 180, 180), self.font_medium, lambda: self.select_option("train")),

            Button("Watch Model", settings.SCREEN_WIDTH // 2 - btn_width // 2, start_y + 2 * (btn_height + btn_spacing), btn_width, btn_height, settings.BUTTON_GRAY, (180, 180, 180), self.font_medium, lambda: self.select_option("watch")),

            Button("Versus Model", settings.SCREEN_WIDTH // 2 - btn_width // 2, start_y + 3 * (btn_height + btn_spacing), btn_width, btn_height, settings.BUTTON_GRAY, (180, 180, 180), self.font_medium, lambda: self.select_option("versus")),

            Button("Quit", settings.SCREEN_WIDTH // 2 - btn_width // 2, start_y + 4 * (btn_height + btn_spacing), btn_width, btn_height, settings.BUTTON_GRAY, (180, 180, 180), self.font_medium, lambda: self.select_option("quit"))
        ]

    def select_option(self, option_key: str):
        self.selected_option = option_key
        self.running = False #sai do menu


    def draw_main_menu(self):
        #titulo
        title_text = self.font_large.render("Game", True, settings.TEXT_COLOR)
        title_rect = title_text.get_rect(center=(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 4))
        self.screen.blit(title_text, title_rect)

        #botoes
        for button in self.buttons:
            button.draw(self.screen)

    def run(self):
        self.running = True
        self.selected_option = None

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.selected_option = "quit"
                    self.running = False

                else:
                    for button in self.buttons:
                        button.handle_event(event)

            self.screen.fill(settings.SKY_BLUE)
            self.draw_main_menu()
            
            pygame.display.flip()
            
        return self.selected_option
        
if __name__ == '__main__':
    pygame.init()
    
    screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
    
    main_menu = MainMenu(screen)

    selected_option = main_menu.run()

    pygame.quit()
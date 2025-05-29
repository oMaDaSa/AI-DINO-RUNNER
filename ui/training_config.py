import pygame
import sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import dino_game.settings as settings

class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, default_val, label, description=None, is_int=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.handle_rect = pygame.Rect(0, 0, 20, height + 6)
        self.min_val = min_val
        self.max_val = max_val
        self.value = default_val
        self.label = label
        self.description = description
        self.is_dragging = False
        self.is_int = is_int
        self.update_handle_position()

    def update_handle_position(self):
        # Calcula a posição do handle com base no valor atual
        val_range = self.max_val - self.min_val
        if val_range == 0:  
            val_range = 1
        normalized_val = (self.value - self.min_val) / val_range
        self.handle_rect.centerx = self.rect.left + int(normalized_val * self.rect.width)
        self.handle_rect.centery = self.rect.centery
    
    def draw(self, surface, font, small_font):
        pygame.draw.rect(surface, settings.COLOR_BUTTON, self.rect, border_radius=4)
        pygame.draw.rect(surface, settings.COLOR_TEXT, self.handle_rect, border_radius=5)
        
        # label
        label_text = font.render(f"{self.label}: {self.format_value()}", True, settings.COLOR_TEXT)
        surface.blit(label_text, (self.rect.left, self.rect.top - 30))
        
        # descrição
        desc_text = small_font.render(self.description, True, (180, 180, 180))
        surface.blit(desc_text, (self.rect.left, self.rect.bottom + 5))
    
    def format_value(self):
        #FORMATA INTEIREO E FLOAT PRA TEXTP
        if self.is_int:
            return str(int(self.value))
        else:
            return f"{self.value:.3f}"
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.handle_rect.collidepoint(event.pos):
                self.is_dragging = True
                return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            self.is_dragging = False
        
        elif event.type == pygame.MOUSEMOTION and self.is_dragging:
            # ATUALIZA VALOR COM BASE NA POSIÇÃO DO MOUSE
            mouse_x = max(self.rect.left, min(event.pos[0], self.rect.right))
            normalized_pos = (mouse_x - self.rect.left) / self.rect.width
            new_value = self.min_val + normalized_pos * (self.max_val - self.min_val)
            
            # Cconverte pra inteiro se for necessário
            if self.is_int:
                new_value = int(new_value)
                
            self.value = new_value
            self.update_handle_position()
            return True
            
        return False
    
class TrainingConfig:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 20)
        self.title_font = pygame.font.Font(None, 50)
        
        self.running = True
        self.config = {}
        
        # dimensoes do botão
        btn_width = 150
        btn_height = 50
        
        # criar os botões de start e cancel
        self.start_button = pygame.Rect(settings.SCREEN_WIDTH // 2 - btn_width - 20, settings.SCREEN_HEIGHT - 80, btn_width, btn_height)
        self.cancel_button = pygame.Rect(settings.SCREEN_WIDTH // 2 + 20, settings.SCREEN_HEIGHT - 80, btn_width, btn_height)
        
        #dimensoes do slider
        slider_width = 300
        slider_height = 10
        slider_x = settings.SCREEN_WIDTH // 2 - slider_width // 2
        start_y = 130
        gap = 70
        
        # criando os sliders
        self.sliders = [
            Slider(slider_x, start_y, slider_width, slider_height, 5, 50, settings.POPULATION_SIZE, "Population Size", "Number of dinosaurs training simultaneously", True),
            
            Slider(slider_x, start_y + gap, slider_width, slider_height, 0.01, 0.5, settings.ALPHA, "Learning Rate (Alpha)", "How quickly the model adapts to new information"),
            
            Slider(slider_x, start_y + 2 * gap, slider_width, slider_height, 0.8, 0.999, settings.GAMMA, "Discount Factor (Gamma)", "How much future rewards are valued compared to immediate rewards"),
            
            Slider(slider_x, start_y + 3 * gap, slider_width, slider_height, 0.9, 1.0, settings.EPSILON_INIT, "Initial Exploration Rate", "Starting probability of choosing random actions"),
            
            Slider(slider_x, start_y + 4 * gap, slider_width, slider_height,  0.9, 0.999, settings.EPSILON_DECAY, "Exploration Decay Rate", "How quickly exploration decreases over time"),
            
            Slider(slider_x, start_y + 5 * gap, slider_width, slider_height,  0.001, 0.1, settings.EPSILON_MIN, "Minimum Exploration Rate", "Lowest exploration rate the agent will reach")
        ]
    
    def get_config(self):
        return {
            "POPULATION_SIZE": int(self.sliders[0].value),
            "ALPHA": self.sliders[1].value,
            "GAMMA": self.sliders[2].value,
            "EPSILON_INIT": self.sliders[3].value,
            "EPSILON_DECAY": self.sliders[4].value,
            "EPSILON_MIN": self.sliders[5].value
        }
    
    def draw(self):
        self.screen.fill(settings.COLOR_SKY)
        
        # titulo
        title_text = self.title_font.render("Training Configuration", True, settings.COLOR_TEXT)
        title_rect = title_text.get_rect(center=(settings.SCREEN_WIDTH // 2, 50))
        self.screen.blit(title_text, title_rect)
        
        # descrições
        desc_text = self.small_font.render("Adjust the parameters below to customize the AI training process", True, settings.COLOR_TEXT)
        desc_rect = desc_text.get_rect(center=(settings.SCREEN_WIDTH // 2, 85))
        self.screen.blit(desc_text, desc_rect)
        
        # sliders
        for slider in self.sliders:
            slider.draw(self.screen, self.font, self.small_font)
        
        #  botoes
        pygame.draw.rect(self.screen, settings.COLOR_GROUND_OBSTACLE, self.start_button, border_radius=8)
        pygame.draw.rect(self.screen, settings.COLOR_FLYING_OBSTACLE, self.cancel_button, border_radius=8)
        
        start_text = self.font.render("Start", True, settings.COLOR_TEXT)
        cancel_text = self.font.render("Cancel", True, settings.COLOR_TEXT)
        
        start_text_rect = start_text.get_rect(center=self.start_button.center)
        cancel_text_rect = cancel_text.get_rect(center=self.cancel_button.center)
        
        self.screen.blit(start_text, start_text_rect)
        self.screen.blit(cancel_text, cancel_text_rect)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return "quit"
            
            # Cada slider checa por evento
            for slider in self.sliders:
                if slider.handle_event(event):
                    break
            
            # Checa evento de mouse click
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.start_button.collidepoint(event.pos):
                    self.running = False
                    return "start"
                
                if self.cancel_button.collidepoint(event.pos):
                    self.running = False
                    return "cancel"
        
        return None
    
    def run(self):
        clock = pygame.time.Clock()
        result = None
        
        while self.running:
            result = self.handle_events()
            if result in ["start", "cancel", "quit"]:
                break
                
            self.draw()
            pygame.display.flip()
            clock.tick(settings.FPS)
        
        if result == "start":
            return self.get_config()
        return None

# Teste
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
    config_screen = TrainingConfig(screen)
    result = config_screen.run()
    print("Config result:", result)
    pygame.quit()

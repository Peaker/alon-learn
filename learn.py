import pygame
import random

antialias = True

CHANNEL_ENDEVENT = pygame.USEREVENT + 1

class Widget:
    def __init__(self, img, pos, click):
        self.img = img
        self.x, self.y = pos
        self.width = self.img.get_width()
        self.height = self.img.get_height()
        self._click = click
        self.top = self.y - self.height // 2
        self.left = self.x - self.width // 2
    def draw(self, screen):
        screen.blit(self.img, (self.left, self.top))
    def click(self, (x, y)):
        if not self.left <= x < self.left + self.width:
            return None
        if not self.top <= y < self.top + self.height:
            return None
        return self._click()

class Letter:
    def __init__(self, font, letter):
        self.letter = letter
        self.img = font.render(letter, antialias, (255, 0, 0))
        self.sound = pygame.mixer.Sound("%s.ogg" % letter.lower())

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.channel = None
        self.font = pygame.font.SysFont(None, 720)
        self.letters = {
            letter: Letter(self.font, letter)
            for letter in "ABC"
        }
        self.press_sound = pygame.mixer.Sound("press.ogg")
        self.yay_sound = pygame.mixer.Sound("yay.ogg")
        self.basa_sound = pygame.mixer.Sound("basa.ogg")
        self.start_round()

    def start_round(self):
        letters = random.sample(self.letters.values(), 3)
        current_chosen = random.choice(letters)

        def please_press():
            def play_chosen_letter():
                self.play(current_chosen.sound)
            self.play(self.press_sound, play_chosen_letter)
        please_press()

        width, height = self.screen.get_size()
        self.qmark = Widget(self.font.render("?", antialias, (255, 0, 0)),
                            (width // 2, height // 2 - 300), please_press)

        self.widgets = [ self.qmark ]

        for i, letter in enumerate(letters):
            def clicked_letter(letter):
                is_right = letter is current_chosen
                def done_feedback():
                    if is_right:
                        self.start_round()
                def click():
                    def play_letter_again():
                        self.play(letter.sound, done_feedback)
                    self.play(self.yay_sound if is_right else self.basa_sound, play_letter_again)
                return click
            self.widgets.append(
                Widget(letter.img,
                       (width // 2 + 350 * (i-1),
                        height // 2 + 300), clicked_letter(letter)))


    def click(self, button, pos):
        for widget in self.widgets:
            res = widget.click(pos)
            if res: return res
        return None

    def play(self, sound, cb = None):
        self.stop_play()
        self.channel = pygame.mixer.Sound.play(sound)
        self.channel.set_endevent(CHANNEL_ENDEVENT)
        self.song_end_cb = cb

    def stop_play(self):
        if self.channel is None:
            return
        self.channel.stop()
        self.channel = None

    def channel_endevent(self):
        self.channel = None
        cb = self.song_end_cb
        self.song_end_cb = None
        if cb is not None:
            cb()

    def draw(self):
        self.screen.fill((0, 0, 0))
        for widget in self.widgets:
            widget.draw(self.screen)
        # text_width = self.qmark.get_width()
        # text_height = self.qmark.get_height()
        # self.screen.blit(self.qmark, (width // 2 - text_width // 2, height // 2 - text_height))
        # self.screen.blit(self.letters["A"], (width // 2 - 4*text_width // 2, height // 2))
        # self.screen.blit(self.letters["B"], (width // 2 - text_width // 2, height // 2))
        # self.screen.blit(self.letters["C"], (width // 2 + 2*text_width // 2, height // 2))

def main():
    pygame.init()
    screen = pygame.display.set_mode((1920, 1200))
    game = Game(screen)
    while True:
        game.draw()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                game.click(event.button, event.pos)
            elif event.type == CHANNEL_ENDEVENT:
                game.channel_endevent()

        pygame.display.flip()
    pygame.quit()

if __name__ == '__main__':
    main()

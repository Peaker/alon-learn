import pygame
import random

antialias = True

CHANNEL_ENDEVENT = pygame.USEREVENT + 1

class Widget:
    def __init__(self, img, topleft, click):
        self.img = img
        self.left, self.top = topleft
        self.width, self.height = self.img.get_size()
        self._click = click
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
        self.channel_end_cb = []
        self.cur_bg_color = (0, 0, 0)
        self.font = pygame.font.SysFont(None, 460)
        self.letters = [Letter(self.font, letter) for letter in "ABCDEFGHIJK"]

        self.streak = self.good = self.bad = 0
        self.subset_size = 3
        self.press_sound = pygame.mixer.Sound("press.ogg")
        self.yay_sound = pygame.mixer.Sound("yay.ogg")
        self.basa_sound = pygame.mixer.Sound("basa.ogg")
        self.start_round()

    def hit(self):
        self.good += 1
        if self.streak < 0:
            self.streak = 0
        self.streak += 1
        if self.streak % 3 == 0:
            self.subset_size += 1
    def miss(self):
        if self.streak > 0:
            self.streak = 0
        self.streak -= 1
        if self.streak % 2 == 0:
            self.subset_size -= 1
            self.subset_size = max(self.subset_size, 3)
        self.bad += 1

    def start_round(self):
        letters = random.sample(self.letters[:self.subset_size], min(6, self.subset_size))
        current_chosen = random.choice(letters)

        def please_press():
            def play_chosen_letter():
                self.play(current_chosen.sound)
            self.play(self.press_sound, play_chosen_letter)
        please_press()

        width, height = self.screen.get_size()
        qmark_img = self.font.render("?", antialias, (255, 0, 0))
        font_height = qmark_img.get_height()
        self.qmark = Widget(
            qmark_img, (width // 2 - qmark_img.get_width()/2,
                        height // 2 - font_height/2), please_press)

        self.widgets = [ self.qmark ]

        pad = 1.2
        avg_letter_width = sum(letter.img.get_width()*pad for letter in letters) / len(letters)
        def letter_width(letter):
            return max(avg_letter_width, letter.img.get_width()*pad)
        letters_widths = map(letter_width, letters)
        letters_width = sum(letters_widths)
        posx = (width - letters_width) / 2
        for letter in letters:
            def clicked_letter(letter, pos, img):
                is_right = letter is current_chosen
                def done_feedback():
                    if is_right:
                        self.start_round()
                def click():
                    if is_right:
                        self.hit()
                        green_rect = pygame.surface.Surface(img.get_size())
                        green_rect.fill((0, 100, 0, 1.0))
                        self.widgets.insert(0, Widget(green_rect, pos, img.get_size()))
                    else:
                        self.miss()
                        self.cur_bg_color = (150, 0, 0)
                    def play_letter_again():
                        self.play(letter.sound, done_feedback)
                    self.play(self.yay_sound if is_right else self.basa_sound, play_letter_again)
                return click
            w = letter_width(letter)
            offset = max(0, w - letter.img.get_width()*pad) / 2
            pos = (posx + offset, height // 2 + font_height/2)
            self.widgets.append(
                Widget(letter.img, pos, clicked_letter(letter, pos, letter.img)))
            posx += w


    def click(self, button, pos):
        widgets = self.widgets[:]
        for widget in widgets:
            res = widget.click(pos)
            if res: return res
        return None

    def play(self, sound, cb = None):
        self.stop_play()
        self.channel = pygame.mixer.Sound.play(sound)
        self.channel.set_endevent(CHANNEL_ENDEVENT)
        self.channel_end_cb.append(cb)

    def stop_play(self):
        if self.channel is None:
            return
        # print("Stopping ", self.channel, " which is busy=", self.channel.get_busy())
        self.channel.stop()
        self.channel = None

    def channel_endevent(self):
        # print("End event")
        self.channel = None
        cb = self.channel_end_cb.pop(0)
        if cb is not None:
            cb()

    def draw(self):
        self.screen.fill(self.cur_bg_color)
        self.cur_bg_color = tuple(component * .9 for component in self.cur_bg_color)
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
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    clock = pygame.time.Clock()
    game = Game(screen)
    while True:
        game.draw()
        clock.tick(40)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                game.click(event.button, event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    return
            elif event.type == CHANNEL_ENDEVENT:
                game.channel_endevent()

        pygame.display.update()
    pygame.quit()

if __name__ == '__main__':
    main()

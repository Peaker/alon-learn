# -*- coding: utf-8 -*-
import pygame
import random
import string
from functools import wraps

antialias = True

CHANNEL_ENDEVENT = pygame.USEREVENT + 1

class Widget:
    def __init__(self, img, topleft, click = None):
        self.img = img
        self.left, self.top = topleft
        self.width, self.height = self.img.get_size()
        assert click is None or callable(click)
        self._click = click
        self.is_hidden = lambda : False
    def draw(self, screen):
        if self.is_hidden():
            return
        screen.blit(self.img, (self.left, self.top))
    def click(self, pos):
        if self.is_hidden():
            return None
        x, y = pos
        if self._click is None:
            return None
        if not self.left <= x < self.left + self.width:
            return None
        if not self.top <= y < self.top + self.height:
            return None
        return self._click()
    @classmethod
    def centered(cls, img, pos, click = None):
        x, y = pos
        return cls(img, (x - img.get_width()/2,
                         y - img.get_height()/2), click)

class Letter:
    def __init__(self, font, letter):
        self.letter = letter
        self.img = font.render(letter, antialias, (255, 0, 0))
        self.sound = pygame.mixer.Sound("audio/%s.ogg" % letter.lower())
        self.hidden = False

def load_img(path, desired_width):
    img = pygame.image.load(path)
    w, h = img.get_size()
    return pygame.transform.scale(img, (desired_width, h * 80 // desired_width))

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.channel = None
        self.channel_end_cb = []
        self.cur_bg_color = (0, 0, 0)
        self.font = pygame.font.Font("../lamdu/lamdu/data/fonts/DejaVuSans.ttf", 240)

        self.smiley_img = load_img("imgs/smiley.jpg", 300)

        self.letters = [Letter(self.font, letter) for letter in string.uppercase]

        self.streak = self.good = self.bad = 0
        self.subset_size = 3
        self.focus = 0 # Start with 'A'
        self.press_sound = pygame.mixer.Sound("audio/press.ogg")
        self.yay_sound = pygame.mixer.Sound("audio/yay.ogg")
        self.basa_sound = pygame.mixer.Sound("audio/basa.ogg")
        self.passed_level_sound = pygame.mixer.Sound("audio/passedlevel.ogg")

        self.qmark_img = self.font.render("?", antialias, (255, 0, 255))
        self.exclmark_img = self.font.render("!", antialias, (0, 255, 0))
        self.font_height = self.qmark_img.get_height()

        self.start_round()

    def hit(self):
        self.good += 1
        if self.streak < 0:
            self.streak = 0
        self.streak += 1
        if self.streak % 3 == 0:
            if self.focus is None:
                self.focus = self.restore_focus
                print("Restored focus to", self.letters[self.focus].letter)
            if self.subset_size < len(self.letters):
                self.subset_size += 1
            if self.focus < self.subset_size - 1:
                self.focus += 1
                print("Moved focus to", self.letters[self.focus].letter)
    def miss(self):
        if self.streak > 0:
            self.streak = 0
        self.streak -= 1
        if self.streak % 2 == 0:
            if self.focus is not None:
                self.restore_focus = max(0, self.focus - 1)
                self.focus = None
            print("Lost focus, will restore to", self.letters[self.restore_focus].letter)
            self.subset_size -= 1
            self.subset_size = max(self.subset_size, 3)
        self.bad += 1

    def start_round(self):
        for letter in self.letters: letter.hidden = False
        assert self.focus < self.subset_size
        letters = random.sample(self.letters[:self.subset_size], min(6, self.subset_size))
        if self.focus is None:
            current_chosen = random.choice(letters)
            print("Chosen random:", current_chosen.letter)
        else:
            current_chosen = focused_letter = self.letters[self.focus]
            if focused_letter not in letters:
                letters[random.choice(range(len(letters)))] = focused_letter

        class state:
            round_complete = False
            @staticmethod
            def unless_complete(f):
                @wraps(f)
                def g(*args, **kw):
                    if state.round_complete:
                        return
                    return f(*args, **kw)
                return g

        width, height = self.screen.get_size()

        @state.unless_complete
        def please_press():
            def play_chosen_letter():
                self.play(current_chosen.sound)
            self.play(self.press_sound, play_chosen_letter)
        please_press()

        self.widgets = [
            Widget(self.smiley_img, (15 + i * self.smiley_img.get_width() * 1.1, 15))
            for i in range(self.streak % 5)]

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
                @state.unless_complete
                def click():
                    self.stop_play()
                    if is_right:
                        state.round_complete = True
                        self.hit()
                        green_rect = pygame.surface.Surface(img.get_size())
                        green_rect.fill((0, 100, 0, 1.0))
                        self.widgets.insert(0, Widget(green_rect, pos))
                        if self.streak % 5 == 0:
                            self.play(self.passed_level_sound, done_feedback)
                            return
                    else:
                        self.miss()
                        self.cur_bg_color = (150, 0, 0)
                    def play_letter_again():
                        self.play(letter.sound, done_feedback)
                    self.play(self.yay_sound if is_right else self.basa_sound, play_letter_again)
                return click
            w = letter_width(letter)
            offset = max(0, w - letter.img.get_width()*pad) / 2
            pos = (posx + offset, height // 2 + self.font_height/2)
            widget = Widget(letter.img, pos, clicked_letter(letter, pos, letter.img))
            widget.is_hidden = lambda letter=letter: letter.hidden
            self.widgets.append(widget)
            posx += w

        @state.unless_complete
        def hint():
            if len(letters) <= 1:
                return
            wrong_letter = random.choice(list(set(letters) - set([current_chosen])))
            wrong_letter.hidden = True
            letters.remove(wrong_letter)

        self.instructions = Widget.centered(
            self.exclmark_img, (width / 2 - 100, height / 2), please_press)
        self.qmark = Widget.centered(self.qmark_img, (width / 2 + 100, height / 2), hint)

        self.widgets.extend((self.instructions, self.qmark))


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

        # Stop means we don't want its callback to take effect:
        self.channel_end_cb[0] = None

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

def main():
    pygame.init()
    screen = pygame.display.set_mode((1920, 1200)) #, pygame.FULLSCREEN)
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

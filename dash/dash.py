# Dash!
# by KidsCanCode 2015
# For educational purposes only
# install pytmx: pip3 install pytmx
import pygame
import sys
import os
import pytmx
# game menu module currently located in above directory
# this adds the parent directory to the path so we can import GameMenu
sys.path.insert(0, '../')
from GameMenu.GameMenu import *

# TODO: level progression
# TODO: level exit
# TODO: explosion on die
# TODO: particles (jump/land)
# TODO: sprite animations?
# TODO: sounds
# TODO: music
# TODO: gravity reversal

# define some colors (R, G, B)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
FUCHSIA = (255, 0, 255)
GRAY = (128, 128, 128)
LIME = (0, 128, 0)
MAROON = (128, 0, 0)
NAVYBLUE = (0, 0, 128)
OLIVE = (128, 128, 0)
PURPLE = (128, 0, 128)
RED = (255, 0, 0)
SILVER = (192, 192, 192)
TEAL = (0, 128, 128)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 128, 0)
CYAN = (0, 255, 255)
BGCOLOR = BLACK

# basic constants for your game options
WIDTH = 640
HEIGHT = 320
FPS = 60
# Game settings
GRAVITY = 1
PLAYER_JUMP = 16
WORLD_SPEED = 8

class SpriteSheet:
    """Utility class to load and parse spritesheets"""
    def __init__(self, filename):
        self.sprite_sheet = pygame.image.load(filename)

    def get_image(self, x, y, width, height):
        # grab an image out of a larger spritesheet
        image = pygame.Surface([width, height], pygame.SRCALPHA, 32).convert_alpha()
        image.blit(self.sprite_sheet, (0, 0), (x, y, width, height))
        # image.set_colorkey(image.get_at((0, 0)))
        return image

class TileRenderer:
    # using PyTMX loads .tmx file generated by Tiled
    def __init__(self, filename):
        tm = pytmx.load_pygame(filename, pixelalpha=True)
        self.size = tm.width * tm.tilewidth, tm.height * tm.tileheight
        self.tmxdata = tm

    def render(self, surface):
        tw = self.tmxdata.tilewidth
        th = self.tmxdata.tileheight
        gt = self.tmxdata.get_tile_image_by_gid

        if self.tmxdata.background_color:
            surface.fill(self.tmxdata.background_color)

        test_img = pygame.Surface([32, 32])
        test_img.fill(GREEN)
        for layer in self.tmxdata.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    tile = gt(gid)
                    if tile:
                        surface.blit(tile, (x*tw, y*th))
                    # else:
                    #     surface.blit(test_img, (x*tw, y*th))
            elif isinstance(layer, pytmx.TiledObjectGroup):
                pass
            elif isinstance(layer, pytmx.TiledImageLayer):
                image = gt(layer.gid)
                if image:
                    surface.blit(image, (0, 0))

    def make_map(self):
        temp_surface = pygame.Surface(self.size)
        self.render(temp_surface)
        return temp_surface

class Player(pygame.sprite.Sprite):
    def __init__(self, game, *groups):
        pygame.sprite.Sprite.__init__(self, *groups)
        self.game = game
        self.vx, self.vy = 0, 0
        self.image = self.game.sprite_sheet.get_image(288, 128, 32, 32)
        self.image_orig = self.image.copy()
        self.rot = 0
        self.rot_speed = 0
        self.rot_cache = {0: self.image}
        self.jumping = False
        self.rect = self.image.get_rect()
        self.rect.bottomleft = (50, HEIGHT-32)
        self.layer = 5

    def update(self):
        self.get_keys()
        self.rotate()
        self.rot = self.rot % 360
        self.vy += GRAVITY

        # move SPEED pixels forward just to see if we're going to hit something
        self.rect.x += self.game.speed / 2
        hits = pygame.sprite.spritecollide(self, self.game.obstacles, False)
        self.rect.x -= self.game.speed / 2
        if hits:
            self.game.speed = 0
            self.game.running = False
        # now move in y and see if we need to land on something
        self.rect.y += self.vy
        hits = pygame.sprite.spritecollide(self, self.game.obstacles, False)
        if hits:
            if hits[0].type == 'platform':
                self.rect.bottom = hits[0].rect.top
                self.vy = 0
                self.jumping = False
            elif hits[0].type == 'spike':
                self.game.speed = 0
                self.game.running = False

        if self.rect.top <= 0:
            self.rect.top = 0
            self.vy = 0
        if self.rect.bottom >= HEIGHT - 32:
            self.rect.bottom = HEIGHT - 32
            self.vy = 0
            self.jumping = False
        if self.rect.top <= 0:
            self.rect.top = 0
            self.vy = 0
            self.jumping = False

    def get_keys(self):
        keystate = pygame.key.get_pressed()
        mousestate = pygame.mouse.get_pressed()
        if keystate[pygame.K_SPACE] or mousestate[0]:
            if not self.jumping:
                self.rect.y -= 1
                self.vy = -PLAYER_JUMP
                self.jumping = True
                self.jump_time = pygame.time.get_ticks()

    def rotate(self):
        if self.jumping:
            self.rot -= 5
        else:
            self.rot = 0
        if self.rot in self.rot_cache:
            image = self.rot_cache[self.rot]
        else:
            image = pygame.transform.rotate(self.image_orig, self.rot)
            self.rot_cache[self.rot] = image
        old_center = self.rect.center
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.center = old_center

class Background(pygame.sprite.Sprite):
    def __init__(self, game, image, x, *groups):
        pygame.sprite.Sprite.__init__(self, *groups)
        self.game = game
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = 0
        self.layer = 0

    def update(self):
        if self.game.speed > 0:
            self.rect.x -= (self.game.speed - 6)

class Blocker(pygame.sprite.Sprite):
    def __init__(self, game, x, y, width, height, obs_type, *groups):
        pygame.sprite.Sprite.__init__(self, *groups)
        self.game = game
        self.type = obs_type
        self.rect = pygame.Rect(x, y, width, height)

    def update(self):
        self.rect.x -= self.game.speed

class Game:
    def __init__(self):
        # initialize game settings
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        # os.environ['SDL_VIDEO_WINDOW_POS'] = '0,0'
        pygame.init()
        # pygame.mixer.init()
        flags = pygame.DOUBLEBUF | pygame.HWSURFACE  # | pygame.FULLSCREEN
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
        pygame.display.set_caption("My Game")
        self.clock = pygame.time.Clock()
        self.load_data()
        font = pygame.font.match_font("Ubuntu Mono")
        self.menu = GameMenu(self, "Dash!", ["Play", "Options", "Quit"], font=font, font_size=30,
                             padding=20)

    def new(self):
        # initialize all your variables and do all the setup for a new game
        self.speed = WORLD_SPEED
        self.all_sprites = pygame.sprite.LayeredUpdates()
        self.backgrounds = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()
        self.level = 1
        # TODO: add per-level loading of tmx
        self.map_surface = self.tile_renderer.make_map()
        self.map_surface.set_colorkey(BLACK)
        self.map_rect = self.map_surface.get_rect()
        for tile_object in self.tile_renderer.tmxdata.objects:
            properties = tile_object.__dict__
            if properties['type'] in ['platform', 'spike']:
                x = properties['x']
                y = properties['y']
                w = properties['width']
                h = properties['height']
                Blocker(self, x, y, w, h, properties['type'], [self.obstacles])
        self.bg1 = Background(self, self.background, 0, self.backgrounds)
        self.bg2 = Background(self, self.background, self.background.get_width(), self.backgrounds)
        self.player = Player(self, self.all_sprites)

    def draw_text(self, text, size, x, y, center=True):
            # utility function to draw text at a given location
            # TODO: move font matching to beginning of file (don't repeat)
            font_name = pygame.font.match_font('arial')
            font = pygame.font.Font(font_name, size)
            text_surface = font.render(text, True, (255, 255, 255))
            text_rect = text_surface.get_rect()
            if center:
                text_rect.midtop = (x, y)
            else:
                text_rect.topleft = (x, y)
            return self.screen.blit(text_surface, text_rect)

    def load_data(self):
        # load all your assets (sound, images, etc.)
        self.background = pygame.image.load('img/game_bg_01_001.png').convert()
        self.background = pygame.transform.scale(self.background, [640, 640])
        self.sprite_sheet = SpriteSheet("img/sprites.png")
        self.tile_renderer = TileRenderer('img/dash2.tmx')

    def run(self):
        # The Game Loop
        self.running = True
        while self.running:
            self.clock.tick(FPS)
            self.events()
            self.update()
            self.draw()

    def quit(self):
        pygame.quit()
        sys.exit()

    def update(self):
        # the update part of the game loop
        if self.bg1.rect.right <= 0:
            self.bg1.rect.left = self.bg2.rect.right
        if self.bg2.rect.right <= 0:
            self.bg2.rect.left = self.bg1.rect.right
        self.backgrounds.update()
        self.all_sprites.update()
        self.map_rect.x -= self.speed
        self.obstacles.update()

    def draw(self):
        # draw everything to the screen
        fps_txt = "FPS: {:.2f}".format(self.clock.get_fps())
        pygame.display.set_caption(fps_txt)
        # self.screen.fill(GREEN)
        self.backgrounds.draw(self.screen)
        self.screen.blit(self.map_surface, self.map_rect)
        self.all_sprites.draw(self.screen)
        pygame.display.flip()

    def events(self):
        # catch all events here
        for event in pygame.event.get():
            # this one checks for the window being closed
            if event.type == pygame.QUIT:
                self.quit()
            # now check for keypresses
            elif event.type == pygame.KEYDOWN:
                # this one quits if the player presses Esc
                if event.key == pygame.K_ESCAPE:
                    self.quit()
                # add any other key events here

    def show_start_screen(self):
        # show the start screen
        self.menu.run()

    def show_go_screen(self):
        # show the game over screen
        pass

g = Game()
while True:
    g.show_start_screen()
    g.new()
    g.run()
    g.show_go_screen()

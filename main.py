from pygame.time import Clock
import cv2
import mediapipe as mp
import pygame
import sys
import math
import random

SCREEN_WIDTH = 1920 - 800
SCREEN_HEIGHT = 1080 - 500
MEAT_TEXTURE = "R/Graphic/Items/1 Icons/Icons_19.png"
MEAT_SPAWN_RATE = 3  # SECONDS
AXE_TEXTURE = "R/Graphic/Items/1 Icons/Icons_09.png"
AXE_SPAWN_RATE = [2,4]

class Location():
    def __init__(self, x, y):
        self.x = x
        self.y = y


class RenderObject():
    def __init__(self):
        self.location = Location(0, 0)
        self.imagePath = ""


class Background():
    def __init__(self, imagePath):
        self.image = pygame.image.load(imagePath).convert()
        self.scroll1 = 0
        self.scroll2 = self.image.get_width()

    def update(self, screen):
        self.scroll1 -= 5
        self.scroll2 -= 5
        if self.scroll1 < self.image.get_width() * -1:
            self.scroll1 = self.image.get_width()
        if self.scroll2 < self.image.get_width() * -1:
            self.scroll2 = self.image.get_width()
        screen.blit(self.image, (self.scroll1, -450))
        screen.blit(self.image, (self.scroll2, -450))


class World():
    def __init__(self, manager, worldname, bgPath):
        self.manager = manager
        self.worldname = worldname
        self.living_entities = []
        self.backgroundImagePath = bgPath
        self.background = Background(self.backgroundImagePath)
        self.points = 0
        self.nextAxeSecond = 0
        self.pause = False

    def update(self, screen):
        # SCROLLING BG
        if not self.pause:
            self.background.update(screen)
        surf = self.manager.font.render(f"Punts: {self.points}", False, (255, 255, 0))
        screen.blit(surf, (surf.get_width(), surf.get_height()))

    def add_new_living_entity(self, entity):
        if not entity in self.living_entities:
            self.living_entities.append(entity)


class WorldManager():
    def __init__(self, **kwargs):
        self.registered_worlds = []
        self.currentActiveWorld = None
        self.points = 0
        self.font = None
        if "font" in kwargs: self.font = kwargs.get("font")

    def getWorldByName(self, name):
        w = None
        for world in self.registered_worlds:
            if world.worldname == name:
                w = world
                break
        return w

    def register_new_world(self, world):
        if not world in self.registered_worlds:
            self.registered_worlds.append(world)

    def changeCurrentActiveWorld(self, name, **kwargs):
        self.currentActiveWorld = self.getWorldByName(name)
        if "player" in kwargs.keys():
            self.currentActiveWorld.add_new_living_entity(kwargs.get("player"))


class Timer():
    def __init__(self, clock):
        self.lastMillis = 0
        self.clock = clock


class ImageSprite(pygame.sprite.Sprite):
    def __init__(self, path, rows, columns, parentObject):
        super().__init__()
        self.path = path
        self.srcImg = pygame.image.load(path)
        self.infAnimation = False
        self.runningAnimation = False
        self.parentObject = parentObject

        # SPRITE DIVISION

        image = pygame.image.load(self.path)
        self.images = []
        for r in range(rows):
            for c in range(columns):
                subsurface = image.subsurface(((image.get_width().real / columns) * c,
                                               (image.get_height().real / rows) * r, image.get_width().real / columns,
                                               image.get_height().real))
                self.images.append(subsurface)
        # ----
        self.imageIndex = 0
        self.image = self.images[self.imageIndex]
        self.rect = self.srcImg.get_rect()
        self.rect.topleft = [parentObject.location.x, parentObject.location.y]

    def update(self):
        if self.runningAnimation:
            self.rect.topleft = [self.parentObject.location.x, self.parentObject.location.y]
            self.imageIndex += 1
            if self.imageIndex >= len(self.images):
                self.imageIndex = 0
                if not self.infAnimation and self.runningAnimation:
                    self.runningAnimation = False
            self.image = self.images[self.imageIndex]

    def setAsInfiniteAnimation(self, b):
        self.runningAnimation = b
        self.infAnimation = b


class AppearingItem(RenderObject):
    def __init__(self, appearanceRange, imagePath):
        super().__init__()
        self.image = pygame.image.load(imagePath).convert()
        self.a_peak = 10
        self.base_location = Location(int(SCREEN_WIDTH * .8), random.randrange(int(SCREEN_HEIGHT * .77),
                                                                               int(SCREEN_HEIGHT * .77) + appearanceRange - self.a_peak))
        self.animated = True

    def isColliding(self, element):
        b = False
        if self.location.x + self.image.get_width() / 2 >= element.location.x >= self.location.x - self.image.get_width() / 2:
            if self.location.y + self.image.get_width() / 2 >= element.location.y >= self.location.y - self.image.get_height() / 2:
                b = True
        return b

    def update(self, screen):
        pass

class LivingEntity(AppearingItem):
    def __init__(self, world: World, appearanceRange, imagePath):
        super().__init__(appearanceRange, imagePath)
        self.world = world

    def destroyEntity(self):
        self.world.living_entities.remove(self)

class Steak(LivingEntity):
    def __init__(self, world: World):
        super().__init__(world,15, MEAT_TEXTURE)
        self.base_location.x = SCREEN_WIDTH
        self.location.x = self.base_location.x
        self.movementSpeed = 7

    def update(self, screen):
        if not self.world.pause:
            self.location.y = min(self.base_location.y + (math.sin(pygame.time.get_ticks() // 200) + 1) * 20,
                                  self.a_peak + self.base_location.y)
            self.location.x = self.location.x - self.movementSpeed
            if self.isColliding(self.world.living_entities[0]):
                self.destroyEntity()
                self.world.points += 1
            if self.location.x < 0: self.destroyEntity()
            screen.blit(self.image, (self.location.x, self.location.y))

class Axe(LivingEntity):
    def __init__(self, world: World):
        super().__init__(world,20, AXE_TEXTURE)
        self.movementSpeed = random.randint(4,10)
        self.base_location.x = SCREEN_WIDTH
        self.location.x = self.base_location.x

    def update(self, screen):
        if not self.world.pause:
            self.location.y = min(self.base_location.y + (math.cos(pygame.time.get_ticks() // 200) + 1) * 20,
                                  self.a_peak + self.base_location.y)
            self.location.x = self.location.x - self.movementSpeed
            if self.isColliding(self.world.living_entities[0]):
                self.destroyEntity()
                self.world.points -= 1
                if self.world.points<0:
                    self.world.pause = True
            screen.blit(self.image, (self.location.x, self.location.y))

    @staticmethod
    def nextAppearingSeconds():
        return random.randint(AXE_SPAWN_RATE[0], AXE_SPAWN_RATE[1])


class PlayerObject(RenderObject):
    def __init__(self):
        super().__init__()
        self.controller = None
        self.baseLocation = Location(SCREEN_WIDTH // 3, int(SCREEN_HEIGHT * .77))
        self.location.x = self.baseLocation.x
        self.location.y = self.baseLocation.y
        self.jumping = False
        self.spriteImage = ImageSprite("R/Graphic/Player/Character/3 Cat/Walk.png", 1, 6, self)
        self.spriteImage.setAsInfiniteAnimation(True)
        self.playerSprite = pygame.sprite.Group()
        self.playerSprite.add(self.spriteImage)
        self.movementSpeed = 8
        self.peakReached = False

    def move(self, x):
        self.location.x += (x * self.movementSpeed)

    def jump(self):
        self.jumping = True
        self.location.y += (1 * self.movementSpeed)

    def isColliding(self, element):
        b = False
        if element.location.x <= self.location.x + self.spriteImage.image.get_width() / 2 and element.location.x >= self.location.x - self.spriteImage.image.get_width() / 2:
            if element.location.y <= self.location.y + self.spriteImage.image.get_width() / 2 and element.location.y >= self.location.y - self.spriteImage.image.get_height() / 2:
                b = True
        return b

    def movementUpdate(self):
        if self.jumping:
            if not self.peakReached:
                if self.location.y > self.baseLocation.y - 60:
                    self.location.y -= (1 * self.movementSpeed)
                else:
                    self.peakReached = True
            else:
                if self.location.y < self.baseLocation.y:
                    self.location.y += (1 * self.movementSpeed)
                else:
                    self.jumping = False
                    self.peakReached = False

    def update(self, screen):
        self.movementUpdate()
        self.playerSprite.draw(screen)
        self.playerSprite.update()


clock = Clock()


def distanceBetween2Points(x, y):
    return abs(math.sqrt((y[0] - x[0]) ** 2 + (y[1] - x[1]) ** 2))


def start():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("TESTING")
    pygame.font.init()
    font = pygame.font.SysFont('Comic Sans MS', 30)

    player = PlayerObject()

    mp_face_mesh = mp.solutions.face_mesh
    cap = cv2.VideoCapture(0)

    timer = Timer(clock)
    axeTimer = Timer(clock)
    worldmanager = WorldManager(font=font)
    worldmanager.register_new_world(
        World(worldmanager, "Forest", "R/Graphic/Background/platformer_background_3/platformer_background_3.png"))
    worldmanager.changeCurrentActiveWorld("Forest", player=player)

    with mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=.6,
            min_tracking_confidence=.5
    ) as face_mesh:

        opMouth = False

        while cap.isOpened():
            s, frame = cap.read()
            if not s:
                print("Missed frame")
                continue
            JUMP_EVENT = pygame.USEREVENT + 1
            frame = cv2.flip(frame, 1)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            r = face_mesh.process(frame)
            if r.multi_face_landmarks:
                lm = r.multi_face_landmarks[0].landmark
                d1, d2, d3, d4 = lm[14], lm[0], lm[10], lm[152]
                if distanceBetween2Points([d1.x, d1.y], [d2.x, d2.y]) / distanceBetween2Points([d3.x, d3.y],
                                                                                               [d4.x, d4.y]) > 0.17:
                    if not opMouth:
                        opMouth = True
                        pygame.event.post(pygame.event.Event(JUMP_EVENT))
                else:
                    if opMouth:
                        opMouth = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == JUMP_EVENT:
                    player.jump()

            # UPDATE------------------------------------------------------------------------------------------

            worldmanager.currentActiveWorld.update(screen)

            # CHECK APPEARING ITEM TIMER
            if pygame.time.get_ticks() > timer.lastMillis + MEAT_SPAWN_RATE * 1000:
                timer.lastMillis = pygame.time.get_ticks()
                worldmanager.currentActiveWorld.add_new_living_entity(Steak(worldmanager.currentActiveWorld))

            if pygame.time.get_ticks()> axeTimer.lastMillis+worldmanager.currentActiveWorld.nextAxeSecond*1000:
                axeTimer.lastMillis = pygame.time.get_ticks()
                worldmanager.currentActiveWorld.add_new_living_entity(Axe(worldmanager.currentActiveWorld))
                worldmanager.currentActiveWorld.nextAxeSecond = Axe.nextAppearingSeconds()

            if worldmanager.currentActiveWorld.pause:
                wins = font.render("Has perdut!", False, (255,255,255))
                screen.blit(wins, (SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
            else:
                for obj in worldmanager.currentActiveWorld.living_entities:
                    obj.update(screen)

            pygame.display.flip()
            clock.tick(25)


if __name__ == "__main__":
    start()

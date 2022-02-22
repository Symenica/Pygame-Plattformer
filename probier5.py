import random
import math
import os
import pygame as pg

# Global Constants
SCREENRECT = pg.Rect(0, 0, 16*32, 480)
SIZE = 32
WALKSPEED = 10
RIGHTMOVE = [1, 3, 5, 3]
LEFTMOVE = [0, 2, 4, 2]
MOVEABLE = ['A', 'B', 'C', 'D','F','G','H','I']
DEADLY = ['B','J']

main_dir = os.path.split(os.path.abspath(__file__))[0]

def load_sound(file):
    """ because pygame can be be compiled without mixer.
    """
    if not pg.mixer:
        return None
    file = os.path.join(main_dir, "data", file)
    try:
        sound = pg.mixer.Sound(file)
        return sound
    except:
        print("Warning, unable to load, %s" % file)
    return None

def loadImage(file):
    """ loads an image, prepares it for play
    """
    file = os.path.join(main_dir, "data", file)
    try:
        surface = pg.image.load(file)
    except:
        raise SystemExit('Could not load image "%s" %s' % (file, pg.get_error()))
    return surface.convert()

def loadSpriteImg(file,x,y):
    img = []
    sheet = loadImage(file)
    sheet.set_colorkey(pg.Color(0,166,80))
    for i in range(0,3,1):
        img.append (pg.Surface([32, 48],pg.SRCALPHA))
        img[2*i].blit(sheet,[0,0,32,48],[x+i*32,y,32,48])
        img.append(pg.transform.flip(img[2*i],True,False))
    img.append(pg.transform.scale(img[2],(32,20)))
    img.append(pg.transform.scale(img[3],(32,20)))
    return img

class TileSprite(pg.sprite.Sprite):
    def __init__(self,img,left,top,type):
        pg.sprite.Sprite.__init__(self, self.containers)
        self.image = img
        self.type = type
        self.rect = pg.Rect(left,top,32,32)
     
class Entity(pg.sprite.Sprite):
    def __init__(self,images,left,top,dir):
        pg.sprite.Sprite.__init__(self, self.containers)
        self.images = images
        self.image = self.images[1]
        self.rect = pg.Rect(left,top,32,48)
        self.dead = False
        self.facing = dir
        self.jumping = False
        self.vx = 0
        self.vy = 0
        self.frame = 0
        self.walkcycle = 0

    def update (self,vxWorld):
        self.rect.move_ip(self.vx-vxWorld, -self.vy)
        if self.jumping == False:
            self.walkcycle = (self.walkcycle + 1) % (WALKSPEED * 4)
            if self.vx > 0:
                self.facing = 1
                self.image = self.images[RIGHTMOVE[self.walkcycle // WALKSPEED]]
                self.vx -= 1
                if self.vx < 0:
                    self.vx = 0
            elif self.vx < 0:
                self.facing = -1
                self.image = self.images[LEFTMOVE[self.walkcycle // WALKSPEED]]
                self.vx += 1
                if self.vx > 0:
                    self.vx = 0
            else:
                if self.facing == 1:
                    self.image = self.images[3]
                else:
                    self.image = self.images[2]
                self.walkcycle = 0
        else:
            if self.facing == 1:
                self.image = self.images[1]
            else:
                self.image = self.images[0]
                self.walkcycle = 0
        if self.vy > -9.5:
            self.vy -= 0.5

    def jumpOver(self):
        self.jumping = False

    def worldCollision(self,W):
        boom = False
        for hit in pg.sprite.spritecollide(self, W, False):
            dist = self.rect.bottom-hit.rect.top
            if (dist < 20) and (dist > 0):
                self.vy = -0.2*self.vy
                self.rect.bottom = hit.rect.top
                self.rect.top = self.rect.bottom-48
                self.jumpOver()
            elif (dist < 32+48) and (dist > 32+48-11):
                self.vy = -0.2*self.vy
                self.rect.top = hit.rect.bottom
                self.rect.bottom = self.rect.top+48
            if hit.type in DEADLY:
                self.dead = True
                boom = True
        for hit in pg.sprite.spritecollide(self, W, False):
            dist = self.rect.right-hit.rect.left
            if (dist < 11) and (dist > 0):
                self.vx = 0
                self.rect.right = hit.rect.left
                self.rect.left = self.rect.right-32
            elif (dist < 64) and (dist > 53):
                self.vx = 0
                self.rect.left = hit.rect.right
                self.rect.right = self.rect.left+32
        return boom

class Player(Entity):
    def __init__(self,images,left,top,dir):
        Entity.__init__(self,images,left,top,dir)
        self.score = 0

    def addScore(self,counts):
        self.score += counts

    def move(self, run, jump, dir, speed):
        self.rect = self.rect.clamp(SCREENRECT)
        if self.jumping == False:
            if run:
                self.vx = dir*speed
            if jump:
                self.vy = -dir*speed
                self.jumping = True
    
    def enemyCollision(self,enemies):
        boom = False
        for hit in pg.sprite.spritecollide(self, enemies, False):
            if (self.vy < -2): 
                self.vx = 0
                self.jumpOver()
                if hit.facing == 1:
                    Corpse(hit.images[7],hit.rect.left,hit.rect.bottom-20)
                else:
                    Corpse(hit.images[6],hit.rect.left,hit.rect.bottom-20)
                hit.kill()
                self.addScore(10)
                boom = True
            else:
                self.dead = True
                boom = True
        return boom

    def die(self):
        self.rect.top += 28
        if self.facing == 1:
            self.image = self.images[7]
        else:
            self.image = self.images[6]

class Enemy(Entity):
    def __init__(self,images,left,top,dir):
        Entity.__init__(self,images,left,top,dir)

    def checkTurn(self,W):
        turn = False
        if self.facing == 1:
            x = self.rect.left + 25
            x1 = self.rect.left + 1
        else:
            x = self.rect.left - 25
            x1 = self.rect.left - 1         
        y = self.rect.bottom
        dummySprite = TileSprite(pg.Surface([0, 0]),x,y,'')
        S = pg.sprite.spritecollide(dummySprite, W, False)

        if S == []:
            turn = True
        elif S[0].type in MOVEABLE:
            dummySprite.rect = pg.Rect(x1,y-48,32,48)
            S = pg.sprite.spritecollide(dummySprite, W, False)
            if S == []:
                turn = False
            if S[0].type in MOVEABLE:
                turn = True
        else:
            turn = True
        dummySprite.kill()
        return turn

    def automove(self,speed,W):
        if self.checkTurn(W):
            self.facing *= -1 
        else:
            self.vx = self.facing * speed

class Corpse(pg.sprite.Sprite):
    def __init__(self,img,left,top):
        pg.sprite.Sprite.__init__(self, self.containers)
        self.image = img
        self.rect = pg.Rect(left,top,32,48)
        self.type = '_'
        self.timer = 20

    def update(self,vxWorld):
        self.rect.move_ip(-vxWorld,0)
        if self.timer > 0:
            self.timer -= 1
            return False
        else:
            return True

class World(pg.sprite.Group):
    level = []
    tiles = []
    lastPos = 0
    
    def __init__(self,all,enemies,corpses):
        self.enemies = enemies
        self.corpses = corpses
        pg.sprite.Group.__init__(self)
        '''
        img = pg.Surface([32, 32])
        img.fill(pg.Color(0,255,255))
        self.tiles.append (['A',img])
        img = pg.Surface([32, 32])
        img.fill(pg.Color(255,255,0))
        self.tiles.append (['B',img])
        img = pg.Surface([32, 32])
        img.fill(pg.Color(200))
        self.tiles.append (['C',img])
        img = pg.Surface([32, 32])
        img.fill(pg.Color(0,0,0))
        self.tiles.append (['D',img])
        '''
        def getTileImg(x,y):
            img = pg.Surface([32, 32],pg.SRCALPHA)
            img.blit(sheet,[0,0,32,32],[4*x+x*32,4*y+y*32,32,32])
            return img

        sheet = loadImage("tiles.png")
        sheet = pg.transform.scale2x(sheet)
        '''
        img = []
        for x in range(0,9,1):
            for y in range(0,12,1):
                img.append (pg.Surface([32, 32],pg.SRCALPHA))
                img[x*12+y].blit(sheet,[0,0,32,32],[4*x+x*32,4*y+y*32,32,32])
        '''
        self.tiles.append (['A',getTileImg(6,4)])
        self.tiles.append (['B',getTileImg(5,1)])
        self.tiles.append (['C',getTileImg(0,0)])
        self.tiles.append (['D',getTileImg(2,0)])
        self.tiles.append (['F',getTileImg(7,8)])
        self.tiles.append (['G',getTileImg(8,8)])
        self.tiles.append (['H',getTileImg(8,1)])
        self.tiles.append (['I',getTileImg(4,0)])
        self.tiles.append (['J',getTileImg(6,1)])
            
        self.level.append ([

            "________________",
            "________________",
            "________________",
            "________________",
            "________________",
            "_______________I",
            "___I______F_____",
            "__________G_____",
            "________F_G_____",
            "________G_G____E",
            "______I_G_G___DD",
            "DDDD____G_G___DD",
            "DDDDB_B_G_GB_BDD",
            "DDDDJBJBGBGJBJDD",
            "HHHHHHHHHHHHHHHH"])
        self.level.append ([
            "________________",
            "________________",
            "________________",
            "_________I______",
            "________________",
            "________________",
            "________________",
            "_______________I",
            "____________F___",
            "________F___G___",
            "____I___G___G__E",
            "DD______G___G__D",
            "DD_B_B_BG_B_G_BD",
            "DDBJBJBJGBJBGBJD",
            "HHHHHHHHHHHHHHHH"])

        TileSprite.containers = self,all
        self.enemySprite = loadSpriteImg("player.png",21+3*32,4*54+11)

        for l in range(2):
            self.addLevel()
     
    def addLevel (self):
        nextLevel = self.level[random.randrange(0,2)]
        y = 0
        for row in(nextLevel):
            x = self.lastPos
            for character in row:
                for knownTiles in self.tiles:
                    if character == knownTiles[0]: #0: known characters
                        TileSprite(knownTiles[1],x,y,character) #1: image of character
                if character == 'E':
                    Enemy(self.enemySprite,x,y-16,1)
                x += 32 #pixels
            y += 32 #pixels
        self.lastPos += 32*16

    def update(self, speed):
        for spr in self.sprites():
            if spr.rect.left < -32:
                spr.kill()
            else:
                spr.rect.move_ip(-speed,0)
        self.lastPos -= speed
        if self.lastPos < (32*16):
            self.addLevel()

        for E in self.enemies:
            E.automove(1,self)
            E.update(speed)
            E.worldCollision(self)
            if E.rect.left < -30:
                E.kill()
        
        for C in self.corpses:
            if C.update(speed) == True:
                C.kill()

class Score(pg.sprite.Sprite):
    """ to keep track of the score.
    """
    def __init__(self):
        pg.sprite.Sprite.__init__(self, self.containers)
        self.font = pg.font.Font(None, 20)
        self.font.set_italic(1)
        self.color = pg.Color("black")
        self.lastscore = -1
        self.update(0)
        self.rect = self.image.get_rect().move(SCREENRECT.right - 100, SCREENRECT.top + 10)

    def update(self,score):
        """ We only update the score in update() when it has changed.
        """
        if score != self.lastscore:
            self.lastscore = score
            msg = "Score: %d" % score
            self.image = self.font.render(msg, 0, self.color)

def main(winstyle=0):
  
    if pg.get_sdl_version()[0] == 2:
        pg.mixer.pre_init(44100, 32, 2, 1024)
    pg.init()
    if pg.mixer and not pg.mixer.get_init():
        print("Warning, no sound")
        pg.mixer = None

    fullscreen = False
    # Set the display mode
    winstyle = 0  # |FULLSCREEN
    bestdepth = pg.display.mode_ok(SCREENRECT.size, winstyle, 32)
    screen = pg.display.set_mode(SCREENRECT.size, winstyle, bestdepth)

    clock = pg.time.Clock()

    # load the sound effects
    boom_sound = load_sound("boom.wav")
    shoot_sound = load_sound("car_door.wav")
    if pg.mixer:
        music = os.path.join(main_dir, "data", "house_lo.wav")
        pg.mixer.music.load(music)
        pg.mixer.music.play(-1)

    all = pg.sprite.RenderUpdates()
    enemies = pg.sprite.Group()
    corpses = pg.sprite.Group()

    Score.containers = all
    Player.containers = all
    Enemy.containers = all, enemies
    Corpse.containers = all, corpses

    S = Score()
    W = World(all,enemies,corpses)
    P = Player(loadSpriteImg("player.png",16+3*32,14*54+32),0,100,1)

    background = loadImage('Mordor.jpg')
    background = pg.transform.scale(background,SCREENRECT.size)
    screen.blit(background, (0, 0))
    pg.display.flip()

    t = 0
    while P.dead == False:
        t+=1
        # get input
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_f:
                    if not fullscreen:
                        print("Changing to FULLSCREEN")
                        screen_backup = screen.copy()
                        screen = pg.display.set_mode(
                            SCREENRECT.size, winstyle | pg.FULLSCREEN, bestdepth
                        )
                        screen.blit(screen_backup, (0, 0))
                    else:
                        print("Changing to windowed mode")
                        screen_backup = screen.copy()
                        screen = pg.display.set_mode(
                            SCREENRECT.size, winstyle, bestdepth
                        )
                        screen.blit(screen_backup, (0, 0))
                    pg.display.flip()
                    fullscreen = not fullscreen


        keystate = pg.key.get_pressed()
        if keystate[pg.K_a]:
            P.move(1,0,-1,3)
        if keystate[pg.K_d]:
            P.move(1,0,1,3)
        if keystate[pg.K_w]:
            P.move(0,1,-1,8)
        if keystate[pg.K_s]:
            P.move(0,1,1,5)
        
        # draw the scene
        all.clear(screen,background)
        if (P.rect.left > (8*32)) and (P.vx > 0):
            W.update(P.vx)
            P.update(P.vx)
        else:
            W.update(0)
            P.update(0)

        if P.worldCollision(W) == True:
            if pg.mixer:
                boom_sound.play()
        P.worldCollision(corpses)
        if P.enemyCollision(enemies) == True:
            if pg.mixer:
                boom_sound.play()
        if P.dead == True:
            P.die()

        S.update(P.score)
        dirty = all.draw(screen)
        pg.display.update(dirty)

        # cap the framerate at 40fps. Also called 40HZ or 40 times per second.
        clock.tick(60)
    P.kill()
    if pg.mixer:
        pg.mixer.music.fadeout(1000)
    pg.time.wait(2000)
    pg.quit()
    
# call the "main" function if running this script
if __name__ == "__main__":
    main()
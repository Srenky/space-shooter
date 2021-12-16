import tkinter as tk
import random as r


class Game(tk.Tk):

    def __init__(self):
        super().__init__()
        self.create_background()
        self.player = Player(self.canvas, game=self)
        #self.asteroid = Asteroid(self.canvas, r.randint(50, 590), -50)
        self.asteroids = []
        self.bindAllEvents()
        self.score = 0
        self.lost = False
        self.scoreId = self.canvas.create_text(
            self.bg.width() - 600, 20, text=f"Score: {self.score}", font='arial', fill="white")

    def create_background(self):
        self.bg = tk.PhotoImage(file="img/background.png")
        self.canvas = tk.Canvas(width=self.bg.width(), height=self.bg.height())
        self.canvas.pack()
        self.canvas.create_image(self.bg.width()/2, self.bg.height()/2,
                                 image=self.bg)

    def timer(self):
        self.player.tik()
        for asteroid in self.asteroids:
            asteroid.tik()
        self.checkStateOfGame()
        if not(self.lost):
            self.canvas.after(50, self.timer)

    def createAsteroid(self):
        if not self.lost:
            self.asteroids.append(
                Asteroid(self.canvas, r.randint(50, 590), -50))
            self.canvas.after(2500, self.createAsteroid)

    def checkStateOfGame(self):
        for rocket in self.player.rockets:
            for asteroid in self.asteroids:
                rocket.didCollide(asteroid, self, self.player)
            rocket.didLeaveScreen(self.player)
        for asteroid in self.asteroids:
            asteroid.didLeaveScreen(self)
            asteroid.didCollide(self, self.player)

    def updateScore(self):
        self.score += 1
        self.canvas.itemconfig(self.scoreId, text=f"Score: {self.score}")

    def bindAllEvents(self):
        self.canvas.bind_all("<KeyPress-Right>", self.player.keyPressRight)
        self.canvas.bind_all("<KeyPress-Left>", self.player.keyPressLeft)
        self.canvas.bind_all("<KeyRelease-Right>", self.player.keyReleaseRight)
        self.canvas.bind_all("<KeyRelease-Left>", self.player.keyReleaseLeft)
        self.canvas.bind_all("<space>", self.player.shoot)

    def gameOver(self):
        self.player.delete()
        for asteroid in self.asteroids:
            asteroid.delete()
        self.canvas.delete(self.scoreId)
        self.canvas.create_text(
            self.bg.width()/2, self.bg.height()/2 - 50, text='GAME OVER', font='arail 50', fill="white")
        self.canvas.create_text(
            self.bg.width()/2, self.bg.height()/2+50, text=f'Score: {self.score}',
            font='arail 30', fill="white")


class Sprite():

    def __init__(self, canvas, x, y):
        self.canvas = canvas
        self.x, self.y = x, y
        self.id = self.canvas.create_image(x, y)
        self.destroyed = False

    def loadSprites(self, filePath, rows, cols):
        spriteImg = tk.PhotoImage(file=filePath)
        sprites = []
        height = spriteImg.height() // rows
        width = spriteImg.width() // cols
        for row in range(rows):
            for col in range(cols):
                l = col*width
                t = row*height
                r = (col+1)*width
                b = (row+1)*height
                subimage = self.createSubimage(spriteImg, l, t, r, b)
                sprites.append(subimage)
        return sprites

    def createSubimage(self, img, left, top, right, bottom):
        subimage = tk.PhotoImage()
        subimage.tk.call(subimage, "copy", img, "-from", left, top, right,
                         bottom, "-to", 0, 0)
        return subimage

    def tik(self):
        pass

    def destroy(self):
        self.destroyed = True
        self.canvas.delete(self.id)


class Asteroid(Sprite):

    def __init__(self, canvas, x, y):
        super().__init__(canvas, x, y)
        self.spriteSheet = self.loadSprites("img/asteroid.png", 1, 6)
        self.canvas.itemconfig(self.id, image=self.spriteSheet[0])
        self.spriteIndex = 0
        self.speed = 3
        self.collision = False

    def tik(self):
        if self.collision:
            self.explode()
            self.speed += 0.1
        else:
            self.move()

    def move(self):
        self.y += self.speed
        self.canvas.coords(self.id, self.x, self.y)

    def nextAnimationIndex(self, index):
        index += 1
        maxIndex = len(self.spriteSheet)
        index = index % maxIndex
        return index

    def didLeaveScreen(self, game):
        if self.y > 550:
            game.asteroids.remove(self)

    def didCollide(self, game, player):
        if self.x-130 < player.x < self.x+130:
            if self.y-65 < player.y < self.y+65:
                game.lost = True
                game.gameOver()

    def delete(self):
        self.destroy()

    def explode(self):
        self.spriteIndex = self.nextAnimationIndex(self.spriteIndex)
        self.canvas.itemconfig(
            self.id, image=self.spriteSheet[self.spriteIndex])
        if self.destroy:
            if self.spriteIndex > 4:
                self.collision = False
                self.canvas.itemconfig(self.id, image=self.spriteSheet[0])
                self.x = r.randint(40, 600)
                self.y = -100


class Rocket(Sprite):

    def __init__(self, canvas, x, y, player):
        super().__init__(canvas, x, y)
        self.spriteSheet = self.loadSprites("img/rocket.png", 1, 1)
        self.canvas.itemconfig(self.id, image=self.spriteSheet[0])
        self.speed = -10
        self.player = player
        self.collision = False
        self.tik()

    def tik(self):
        if self.collision:
            self.explode()
        else:
            self.move()

    def move(self):
        self.y += self.speed
        self.canvas.coords(self.id, self.x, self.y)
        self.canvas.after(50, self.tik)

    def didCollide(self, asteroid, game, player):
        if asteroid.x-50 < self.x < asteroid.x+50:
            if asteroid.y-50 < self.y < asteroid.y+50:
                self.collision = True
                asteroid.collision = True
                player.rockets.remove(self)
                self.explode()
                game.updateScore()

    def didLeaveScreen(self, player):
        if self.y < 0:
            player.rockets.remove(self)
            self.collision = True

    def explode(self):
        self.canvas.delete(self.id)


class Player(Sprite):

    def __init__(self, canvas, game, x=320, y=430):
        super().__init__(canvas, x, y)
        self.spriteSheet = self.loadAllSprites()
        self.spriteIndex = 0
        self.dx = 0
        self.rockets = []
        self.game = game

    def loadAllSprites(self):
        spriteSheet = []
        spriteSheet = self.loadSprites("img/player.png", 1, 16)
        return spriteSheet

    def nextAnimationIndex(self, index):
        index += 1
        maxIndex = len(self.spriteSheet)
        index = index % maxIndex
        return index

    def tik(self):
        self.spriteIndex = self.nextAnimationIndex(self.spriteIndex)
        img = self.spriteSheet[self.spriteIndex]
        self.canvas.itemconfig(self.id, image=img)
        self.move()

    def move(self):
        x = self.x + self.dx
        y = self.y
        if x >= 30 and x <= self.canvas.winfo_width()-30:
            self.x = x
        self.canvas.coords(self.id, x, y)

    def shoot(self, event):
        if not game.lost:
            self.rockets.append(Rocket(self.canvas, self.x,
                                       self.y - self.spriteSheet[0].height() / 2 + 10, self))

    def keyPressRight(self, event):
        self.dx = 10

    def keyReleaseRight(self, event):
        self.dx = 0

    def keyPressLeft(self, event):
        self.dx = -10

    def keyReleaseLeft(self, event):
        self.dx = 0

    def delete(self):
        self.destroy()


game = Game()
game.timer()
game.createAsteroid()

game.mainloop()

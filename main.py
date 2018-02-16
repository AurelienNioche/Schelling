# -*- coding: utf-8 -*-
from __future__ import division
import numpy as np
import os
from PIL import Image  # pip install pillow
from tkinter import Tk, Canvas
import cv2  # pip install opencv-python
import tqdm
import shutil

'''
Schelling version 3:
Don't show anything, just print it in a ps file
'''


class GameBoard(Tk):

    # Parameters
    #
    # Authors: mesh ; repartition ; (square_size)
    # Schelling (1971): 13*16 ; 69, 69, 70 ; (50)
    # Vinkovic & Kirman (2006): 100*100 ; 4000, 4000, 2000
    # (me!): 26*32 ; 25 ; 276, 276, 280

    mesh = 100, 100
    square_size = 7
    window_size = mesh[1] * square_size, mesh[0] * square_size
    case_number = mesh[0] * mesh[1]
    x_coordinates = np.arange(0, window_size[0], square_size)
    y_coordinates = np.arange(0, window_size[1], square_size)

    repartition = [4000, 4000, 2000]

    tolerance = 1 / 2

    # Images folder
    folder = "schellingCaptures"
    folder_postscript = os.path.join(folder, 'postscript')
    folder_jpg = os.path.join(folder, 'jpg')

    for f in folder_postscript, folder_jpg:
        os.makedirs(f, exist_ok=True)

    video_name = 'schelling.avi'

    video_fps = 30

    def __init__(self, save=True, t_max=None, conserve_pictures=False):

        Tk.__init__(self)

        self.save = save
        self.t_max = t_max
        self.conserve_pictures = conserve_pictures

        # ----------------- #

        self.canvas = Canvas(self, width=self.window_size[0], height=self.window_size[1])

        self.cases = []
        self.target = None
        self.t = 0

        print("\nRunning...\n")

        if self.t_max is not None:
            self.pbar = tqdm.tqdm(total=self.t_max)

        self.build_cases()
        self.run()

    def build_cases(self):

        colors = \
            ["blue"]*self.repartition[0] + \
            ["red"]*self.repartition[1] + \
            ["white"]*self.repartition[2]

        np.random.shuffle(colors)

        c = 0
        for i, row in enumerate(range(self.mesh[0])):

            self.cases.append([])

            for column in range(self.mesh[1]):

                self.cases[i].append(
                    Case(
                        canvas=self.canvas, position=(row, column), color=colors[c],
                        x_coordinates=self.x_coordinates, y_coordinates=self.y_coordinates,
                        square_size=self.square_size, mesh=self.mesh
                         ))
                c += 1
        self.canvas.pack()

    def run(self):

        self.select_a_case()

        if not self.satisfied(case=self.target, desired_color=self.target.color):

            self.try_to_find_a_new_place()

        if self.save:
            self.record()

        self.t += 1

        # Progress bar if t_max is defined
        if self.t_max is not None:
            self.pbar.update()

        # Close window if t_max is reached
        if self.t == self.t_max:
            self.destroy()
            self.pbar.close()

        else:
            self.after(1, self.run)

    def select_a_case(self):

        search = True
        while search:

            r = np.random.choice(range(self.mesh[0]))
            c = np.random.choice(range(self.mesh[1]))
            self.target = self.cases[r][c]
            if self.target.color != "white":
                search = False

    def satisfied(self, case, desired_color):

        n_colors = []

        for i in case.neighborhood:
            n_colors.append(self.cases[i[0]][i[1]].color)

        red = n_colors.count("red")
        blue = n_colors.count("blue")

        satisfied = 0

        if desired_color == "red":
            if red != 0:
                ratio = blue/red
                if ratio > self.tolerance:
                    satisfied = 0
                else:
                    satisfied = 1
            else:
                if blue > 0:
                    satisfied = 0
                else:
                    satisfied = 1
        elif desired_color == "blue":

            if blue != 0:

                ratio = red/blue

                if ratio > self.tolerance:
                    satisfied = 0
                else:
                    satisfied = 1
            else:
                if red > 0:
                    satisfied = 0
                else:
                    satisfied = 0

        return satisfied

    def try_to_find_a_new_place(self):

        p = 1
        search = True
        while search:

            if p == 1:
                cases_to_check = self.target.neighborhood
            else:
                cases_to_check = self.define_cases_to_check(p)

            if cases_to_check:

                satisfying_places = self.find_satisfying_places(cases_to_check)
                if satisfying_places:
                    self.change_place(satisfying_places)
                    search = False
                else:
                    p += 1
            else:
                search = False

    def change_place(self, satisfying_places):

        np.random.shuffle(satisfying_places)
        self.cases[satisfying_places[0][0]][satisfying_places[0][1]].color = self.target.color
        self.cases[satisfying_places[0][0]][satisfying_places[0][1]].update_color()
        self.target.color = "white"
        self.target.update_color()

    def define_cases_to_check(self, perimeter):

        cases_to_check = []

        r = self.target.position[0]
        c = self.target.position[1]
        p = perimeter

        # Begin by adding the left strip and right strip
        for i in range(r-p, r+p+1):
            for j in [c-p, c+p]:

                if i in range(self.mesh[0]) and j in range(self.mesh[1]):

                    cases_to_check.append((i, j))
                else:
                    pass

        # Continue by adding the top and bottom strip
        for i in [r-p, r+p]:
            for j in range(c-p+1, c+p):

                if i in range(self.mesh[0]) and j in range(self.mesh[1]):

                    cases_to_check.append((i, j))
                else:
                    pass

        return cases_to_check

    def find_satisfying_places(self, cases_to_check):

        new_potential_places = []

        for i in cases_to_check:

            if self.cases[i[0]][i[1]].color == "white" and \
                    self.satisfied(case=self.cases[i[0]][i[1]], desired_color=self.target.color):

                new_potential_places.append(i)
            else:
                pass

        return new_potential_places

    def record(self):

        self.canvas.postscript(
            file=os.path.join(self.folder_postscript, "image%04d.ps" % (self.t,)),
            colormode='color',
            width=self.window_size[0],
            height=self.window_size[1])

    def convert_images(self):

        print("\nConvert postscript images into jpg...\n")

        images = [img for img in os.listdir(self.folder_postscript) if img.endswith(".ps")]

        for i in tqdm.tqdm(images):

            im = Image.open(os.path.join(self.folder_postscript, i))
            im.save(os.path.join(self.folder_jpg, "".join((i.split(".")[0], ".jpg"))))

    def make_video(self):

        print("\nCreating video...\n")

        images = [img for img in os.listdir(self.folder_jpg) if img.endswith(".jpg")]

        frame = cv2.imread(os.path.join(self.folder_jpg, images[0]))
        height, width, layers = frame.shape

        video = cv2.VideoWriter(self.video_name, cv2.VideoWriter_fourcc(*'XVID'), self.video_fps, (width, height))

        for image in tqdm.tqdm(images):
            video.write(cv2.imread(os.path.join(self.folder_jpg, image)))

        cv2.destroyAllWindows()
        video.release()

    def remove_capture_folder(self):

        shutil.rmtree(self.folder)


class Case:

    def __init__(self, canvas, position, color,
                 x_coordinates, y_coordinates, square_size, mesh):

        self.canvas = canvas
        self.position = position
        self.color = color

        self.shape = self.canvas.create_rectangle(
            x_coordinates[self.position[1]],
            y_coordinates[self.position[0]],
            x_coordinates[self.position[1]] + square_size,
            y_coordinates[self.position[0]] + square_size,
            fill=self.color, width=0)

        self.possible_neighborhood = \
            [(self.position[0], self.position[1]+1),
             (self.position[0]+1, self.position[1]+1),
             (self.position[0]+1, self.position[1]),
             (self.position[0]+1, self.position[1]-1),
             (self.position[0], self.position[1]-1),
             (self.position[0]-1, self.position[1]-1),
             (self.position[0]-1, self.position[1]),
             (self.position[0]-1, self.position[1]+1)]

        self.neighborhood = []

        for i in self.possible_neighborhood:

            if i[0] in range(mesh[0]) and i[1] in range(mesh[1]):

                self.neighborhood.append(i)
            else:
                pass

    def update_color(self):

        self.canvas.itemconfig(
            self.shape,
            fill=self.color)


if __name__ == "__main__":

    game = GameBoard(save=False, t_max=None, conserve_pictures=False)
    game.mainloop()

    if game.save:
        game.convert_images()
        game.make_video()
        if not game.conserve_pictures:
            game.remove_capture_folder()

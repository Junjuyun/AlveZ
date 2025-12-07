import pygame
from game import Game  # new module where main Game class lives

def main():
    pygame.init()
    Game().run()

if __name__ == "__main__":
    main()

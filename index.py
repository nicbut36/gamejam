import random
import time
import pygame as pg
from random import randrange
import pymunk.pygame_util

pymunk.pygame_util.positive_y_is_up = False

RES = WIDTH, HEIGHT = 540, 960
FPS = 60
pg.init()
surface = pg.display.set_mode(RES)
clock = pg.time.Clock()
draw_options = pymunk.pygame_util.DrawOptions(surface)
draw_options.flags = draw_options.DRAW_SHAPES

space = pymunk.Space()
space.gravity = 0, 800

pg.font.init()
font = pg.font.SysFont('Arial', 30)
title_font = pg.font.SysFont('Arial', 50)

start_time = 0
game_started = False
game_paused = False
pause_start_time = 0
paused_duration = 0
game_over = False
game_finish_time = 0

play_button = pg.Rect(WIDTH//2 - 100, HEIGHT//2 - 25, 200, 50)
play_button_color = (0, 200, 0)
play_text = font.render("Играть", True, (255, 255, 255))

segment_shape = pymunk.Segment(space.static_body, (2, HEIGHT), (WIDTH, HEIGHT), 26)
space.add(segment_shape)
segment_shape.elasticity = 0.1
segment_shape.friction = 1.0

forms = [
    [(50,50), (50,-50), (-50,-50), (-50,50)],
    [(100,50), (100,-50), (-100,-50), (-100,50)],
    [(50,100), (-50,100), (-50,-100), (50,-100)],
    [(100,100), (100,-100), (-100,-100), (-100,100)],
    [(25,25), (25,-25), (-25,-25), (-25,25)],
    [(50,25), (50,-25), (-50,-25), (-50,25)],
    [(25,50), (-25,50), (-25,-50), (25,-50)]
]

tracked_blocks = {}

black_band = pymunk.Segment(space.static_body, (0, 250), (WIDTH, 250), 2)
space.add(black_band)
black_band.sensor = True
black_band.color = pg.Color(0,0,0)

ghost_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
ghost_body.position = (0, 100)
ghost_shape = pymunk.Poly(ghost_body, [(-50, -50), (-50, -20), (50, -20), (50, -50)])
ghost_shape.sensor = True
ghost_shape.color = (255, 0, 0, 150)
space.add(ghost_body, ghost_shape)
ghost_body.left_bound = 100
ghost_body.right_bound = WIDTH-100
ghost_body.speed = 200
ghost_body.direction = 1

remaining = 0
last_tick = 0

running = True
while running:
    current_time = pg.time.get_ticks()
    
    if game_started and remaining > 0 and not game_paused:
        remaining = max(0, remaining - (current_time - last_tick) / 1000)
    last_tick = current_time

    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
        
        if event.type == pg.MOUSEBUTTONDOWN:
            if not game_started and play_button.collidepoint(event.pos):
                game_started = True
                start_time = time.time()
                game_over = False

    keys = pg.key.get_pressed()
    if game_started and keys[pg.K_SPACE] and remaining == 0 and not game_paused:
        points = random.choice(forms)
        square_body = pymunk.Body(1, pymunk.moment_for_poly(1, points))
        square_body.position = (ghost_body.position[0], ghost_body.position[1]-400)
        square_shape = pymunk.Poly(square_body, points)
        square_shape.elasticity = 0.4
        square_shape.friction = 1.0
        square_shape.color = [randrange(256) for _ in range(4)]
        space.add(square_body, square_shape)
        tracked_blocks[square_body] = {'start_time': None, 'reported': False}
        remaining = 2

    if game_started and not game_paused:
        space.step(1 / FPS)
    
    if game_started and not game_paused:
        ghost_body.position += (ghost_body.speed * ghost_body.direction / FPS, 0)
        if ghost_body.position.x >= ghost_body.right_bound:
            ghost_body.direction = -1
        elif ghost_body.position.x <= ghost_body.left_bound:
            ghost_body.direction = 1

    if game_started and not game_paused and not game_over:
        current_check_time = time.time()
        for body, data in list(tracked_blocks.items()):
            if body.position.y > 250:
                data['start_time'] = None
                data['reported'] = False
            else:
                if data['start_time'] is None:
                    data['start_time'] = current_check_time
                elif not data['reported'] and (current_check_time - data['start_time']) >= 1:
                    game_over = True
                    game_finish_time = current_check_time - start_time - paused_duration

    if game_over:
        game_started = False
        game_paused = False
        start_time = 0
        paused_duration = 0
        
        for body in list(tracked_blocks.keys()):
            space.remove(body, *body.shapes)
        tracked_blocks.clear()
        
        space.remove(ghost_body, ghost_shape)
        ghost_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        ghost_body.position = (0, 100)
        ghost_shape = pymunk.Poly(ghost_body, [(-50, -50), (-50, -20), (50, -20), (50, -50)])
        ghost_shape.sensor = True
        ghost_shape.color = (255, 0, 0, 150)
        space.add(ghost_body, ghost_shape)
        ghost_body.left_bound = 100
        ghost_body.right_bound = WIDTH-100
        ghost_body.speed = 200
        ghost_body.direction = 1

    if game_started:
        surface.fill(pg.Color('grey'))
        space.debug_draw(draw_options)
        
        if not game_paused:
            current_time = (time.time() - start_time) - paused_duration
        else:
            current_time = (pause_start_time - start_time) - paused_duration
        
        timer_text = f"{int(current_time // 60):02d}:{int(current_time % 60):02d}"
        surface.blit(font.render(timer_text, True, (255, 255, 255)), (WIDTH - 100, 20))
        
        if game_paused:
            pause_text = font.render("PAUSED", True, (255, 0, 0))
            surface.blit(pause_text, (WIDTH//2 - pause_text.get_width()//2, 50))
    else:
        surface.fill((50, 50, 50))
        
        if game_over:
            minutes = int(game_finish_time // 60)
            seconds = int(game_finish_time % 60)
            title = title_font.render("Игра Окончена", True, (255, 0, 0))
            time_text = font.render(f"Ваше время: {minutes:02d}:{seconds:02d}", True, (255, 255, 255))
            surface.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//3 - 100))
            surface.blit(time_text, (WIDTH//2 - time_text.get_width()//2, HEIGHT//3 - 30))
        else:
            title = title_font.render("Гравитационная игра", True, (255, 255, 255))
            surface.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//3 - 50))
        
        pg.draw.rect(surface, play_button_color, play_button)
        surface.blit(play_text, (play_button.x + 50 - play_text.get_width()//2, play_button.y + 25 - play_text.get_height()//2))

    pg.display.flip()
    clock.tick(FPS)

pg.quit()
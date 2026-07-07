"""
particles.py
============
A lightweight particle system used purely for visual flair:

- "Anti-gravity" particles: small glowing sparks spawned at the cursor
  while actively drawing, which drift *upward* (negative gravity) and
  fade out -- reinforcing the neon, futuristic feel.
- Ambient floating particles: a sparse field of slow-drifting particles
  that spawn across the whole frame over time, independent of drawing,
  for a living, "digital dust" background effect.

Rendered onto its own transparent-black layer each frame and additively
blended into the final composite by main.py.
"""

import random

import cv2
import numpy as np

import config


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "radius")

    def __init__(self, x, y, vx, vy, life, color, radius):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color
        self.radius = radius

    def update(self):
        self.x += self.vx
        self.y += self.vy
        # "Anti-gravity": particles accelerate gently upward and slow their
        # horizontal drift over time, rather than falling like real sparks.
        self.vy -= 0.03
        self.vx *= 0.98
        self.life -= 1

    @property
    def alive(self):
        return self.life > 0

    @property
    def alpha(self):
        return max(0.0, self.life / self.max_life)


class ParticleSystem:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.particles = []

    def emit_at(self, point, color, count: int = config.PARTICLES_PER_DRAW_EVENT):
        """Spawn a small burst of sparks at the given drawing point."""
        if len(self.particles) >= config.PARTICLE_MAX_COUNT:
            return
        for _ in range(count):
            angle = random.uniform(0, 2 * np.pi)
            speed = random.uniform(config.PARTICLE_MIN_SPEED, config.PARTICLE_MAX_SPEED)
            vx = np.cos(angle) * speed
            vy = np.sin(angle) * speed - 0.4  # slight initial upward bias
            life = random.randint(config.PARTICLE_MIN_LIFETIME, config.PARTICLE_MAX_LIFETIME)
            radius = random.randint(1, 3)
            self.particles.append(Particle(point[0], point[1], vx, vy, life, color, radius))

    def spawn_ambient(self):
        """Occasionally spawn a slow-drifting background particle anywhere on screen."""
        if len(self.particles) >= config.PARTICLE_MAX_COUNT:
            return
        if random.random() > config.AMBIENT_PARTICLE_SPAWN_CHANCE:
            return
        x = random.uniform(0, self.width)
        y = random.uniform(0, self.height)
        vx = random.uniform(-0.3, 0.3)
        vy = random.uniform(-0.6, -0.1)
        life = random.randint(config.PARTICLE_MIN_LIFETIME, config.PARTICLE_MAX_LIFETIME * 2)
        color = random.choice(config.COLOR_PALETTE)[1]
        self.particles.append(Particle(x, y, vx, vy, life, color, 1))

    def update(self):
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alive]

    def render(self):
        """Return a black BGR layer with all particles drawn, ready for additive blending."""
        layer = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        for p in self.particles:
            if not (0 <= p.x < self.width and 0 <= p.y < self.height):
                continue
            color = tuple(int(c * p.alpha) for c in p.color)
            cv2.circle(layer, (int(p.x), int(p.y)), p.radius, color, -1, lineType=cv2.LINE_AA)
        return layer

    def clear(self):
        self.particles = []

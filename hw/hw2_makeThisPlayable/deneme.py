import turtle
import math
import random
from abc import ABC, abstractmethod
from typing import Dict, Tuple, List, Optional

# Global constants for the screen/canvas boundaries
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SHAPES: List["Polygon"] = []  # Global list to hold all Polygon objects
ANIMATION_DELAY_MS = 20  # 50 fps

# Game constants & state
COLOR_HEX: Dict[str, str] = {
    "r": "#FF3B30",
    "g": "#34C759",
    "b": "#1E90FF",
    "y": "#FFCC00",
}

INITIAL_COUNTS: Dict[str, int] = {"r": 5, "g": 5, "b": 5, "y": 5}

MASS_MODE: str = "equal"
RULES_OVERLAY_ACTIVE: bool = False

HUD_TURTLE: Optional[turtle.Turtle] = None

RULE_OPTIONS: List[str] = [
    "noop",
    "both_disappear",
    "a_disappear",
    "b_disappear",
    "a->r",
    "a->g",
    "a->b",
    "a->y",
    "b->r",
    "b->g",
    "b->b",
    "b->y",
]
COLORS_ORDER: List[str] = ["r", "g", "b", "y"]
COLLISION_RULES: Dict[Tuple[str, str], str] = {
    (min(a, b), max(a, b)): "noop"
    for a in COLORS_ORDER
    for b in COLORS_ORDER
}


def draw_dashed_circle(t, x, y, radius):
    t.up()
    t.goto(x, y - radius)
    t.color("gray")
    t.pensize(1)
    segments = 30
    segment_angle = 360 / segments
    t.setheading(0)
    for i in range(segments):
        if i % 2 == 0:
            t.down()
        else:
            t.up()
        t.circle(radius, segment_angle)
    t.up()


class VelocityVector:
    def __init__(self, vx, vy):
        self.vx = vx
        self.vy = vy

    def __add__(self, other):
        if isinstance(other, VelocityVector):
            return VelocityVector(self.vx + other.vx, self.vy + other.vy)
        return NotImplemented

    def __repr__(self):
        return f"VelocityVector(vx={self.vx:.2f}, vy={self.vy:.2f})"

    @property
    def speed(self):
        return math.hypot(self.vx, self.vy)


class CanvasHost:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    @property
    def dimensions(self):
        return {"w": self.width, "h": self.height}


CANVAS = CanvasHost(SCREEN_WIDTH, SCREEN_HEIGHT)


class Polygon(ABC):
    active_count = 0
    DRAW_BOUNDING_CIRCLE = True

    def __init__(self, x, y, edges, size, color):
        self.x = x
        self.y = y
        self.edges = edges
        self._size = size
        self.color = color
        self.color_key = "r"
        speed = random.uniform(1, 3)
        angle = random.uniform(0, 2 * math.pi)
        self.velocity = VelocityVector(
            vx=speed * math.cos(angle), vy=speed * math.sin(angle)
        )
        Polygon.active_count += 1
        self.show_circle = Polygon.DRAW_BOUNDING_CIRCLE

    def __del__(self):
        Polygon.active_count -= 1

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, new_size):
        if new_size > 0:
            self._size = new_size
        else:
            raise ValueError("Polygon size must be positive.")

    def update_position(self):
        self.x += self.velocity.vx
        self.y += self.velocity.vy

    @abstractmethod
    def bounding_radius(self) -> float:
        raise NotImplementedError

    def mass(self) -> float:
        if MASS_MODE == "equal":
            return 1.0
        R = self.bounding_radius()
        area = 0.5 * self.edges * (R ** 2) * math.sin(2 * math.pi / self.edges)
        return max(0.1, area / 100.0)

    @abstractmethod
    def draw(self, t):
        pass

    @abstractmethod
    def move(self, canvas):
        pass


class Triangle(Polygon):
    def __init__(self, x, y):
        super().__init__(x, y, 3, 22, COLOR_HEX["r"])
        self.color_key = "r"
        self.velocity = random_velocity_for_color(self.color_key)

    def draw(self, t):
        if self.show_circle:
            draw_dashed_circle(t, self.x, self.y, self.bounding_radius())
        t.up()
        t.goto(self.x, self.y)
        t.goto(self.x + self.size, self.y)
        t.down()
        t.color("white", self.color)
        t.begin_fill()
        for _ in range(self.edges):
            t.forward(self.size * 1.732)
            t.left(360 / self.edges)
        t.end_fill()

    def move(self, canvas):
        self.update_position()
        w, h = canvas.dimensions["w"] / 2, canvas.dimensions["h"] / 2
        s = self.bounding_radius()
        if self.x + s > w or self.x - s < -w:
            self.velocity.vx *= -1
            self.x = max(-w + s, min(self.x, w - s))
        if self.y + s > h or self.y - s < -h:
            self.velocity.vy *= -1
            self.y = max(-h + s, min(self.y, h - s))

    def bounding_radius(self):
        return self.size * 1.5


class Square(Polygon):
    def __init__(self, x, y):
        super().__init__(x, y, 4, 30, COLOR_HEX["b"])
        self.color_key = "b"
        self.velocity = random_velocity_for_color(self.color_key)

    def draw(self, t):
        if self.show_circle:
            draw_dashed_circle(t, self.x, self.y, self.bounding_radius())
        t.up()
        t.goto(self.x - self.size / 2, self.y - self.size / 2)
        t.down()
        t.color("white", self.color)
        t.begin_fill()
        for _ in range(self.edges):
            t.forward(self.size)
            t.left(90)
        t.end_fill()

    def move(self, canvas):
        self.update_position()
        w, h = canvas.dimensions["w"] / 2, canvas.dimensions["h"] / 2
        s = self.size / 2
        if self.x > w + s:
            self.x = -w - s
        elif self.x < -w - s:
            self.x = w + s
        if self.y > h + s:
            self.y = -h - s
        elif self.y < -h - s:
            self.y = h + s

    def bounding_radius(self):
        return (self.size * math.sqrt(2)) / 2


class Pentagon(Polygon):
    def __init__(self, x, y):
        super().__init__(x, y, 5, 26, COLOR_HEX["g"])
        self.color_key = "g"
        self.velocity = random_velocity_for_color(self.color_key)

    def draw(self, t):
        if self.show_circle:
            draw_dashed_circle(t, self.x, self.y, self.bounding_radius())
        t.up()
        t.goto(self.x, self.y)
        t.goto(self.x + self.size, self.y)
        t.setheading(90)
        t.down()
        t.color("white", self.color)
        t.begin_fill()
        for _ in range(self.edges):
            t.forward(self.size)
            t.left(360 / self.edges)
        t.end_fill()

    def move(self, canvas):
        self.update_position()
        w, h = canvas.dimensions["w"] / 2, canvas.dimensions["h"] / 2
        s = self.bounding_radius()
        if self.x + s > w or self.x - s < -w:
            self.velocity.vx *= -1
            self.x = max(-w + s, min(self.x, w - s))
        if self.y + s > h or self.y - s < -h:
            self.velocity.vy *= -1
            self.y = max(-h + s, min(self.y, h - s))

    def bounding_radius(self):
        return self.size * 1.1


class Hexagon(Polygon):
    def __init__(self, x, y):
        super().__init__(x, y, 6, 26, COLOR_HEX["y"])
        self.color_key = "y"
        self.velocity = random_velocity_for_color(self.color_key)

    def draw(self, t):
        if self.show_circle:
            draw_dashed_circle(t, self.x, self.y, self.bounding_radius())
        t.up()
        t.goto(self.x, self.y)
        t.goto(self.x + self.size, self.y)
        t.setheading(90)
        t.down()
        t.color("white", self.color)
        t.begin_fill()
        for _ in range(self.edges):
            t.forward(self.size)
            t.left(360 / self.edges)
        t.end_fill()

    def move(self, canvas):
        self.update_position()
        w, h = canvas.dimensions["w"] / 2, canvas.dimensions["h"] / 2
        s = self.size / 2
        if self.x > w + s:
            self.x = -w - s
        elif self.x < -w - s:
            self.x = w + s
        if self.y > h + s:
            self.y = -h - s
        elif self.y < -h - s:
            self.y = h + s

    def bounding_radius(self):
        return self.size


def cycle_rule_for_cell(c1: str, c2: str):
    key = (min(c1, c2), max(c1, c2))
    current = COLLISION_RULES.get(key, "noop")
    idx = (RULE_OPTIONS.index(current) + 1) % len(RULE_OPTIONS)
    COLLISION_RULES[key] = RULE_OPTIONS[idx]


def handle_click_main(x, y):
    """Click handler for the main canvas."""
    if RULES_OVERLAY_ACTIVE:
        # In main canvas, clicks do nothing when overlay active
        return

    nearest_idx = -1
    nearest_dist = float("inf")
    for idx, s in enumerate(SHAPES):
        r = s.bounding_radius()
        d = math.hypot(x - s.x, y - s.y)
        if d <= r and d < nearest_dist:
            nearest_idx = idx
            nearest_dist = d
    if nearest_idx >= 0:
        SHAPES[nearest_idx].show_circle = not SHAPES[nearest_idx].show_circle


def handle_click_menu(x, y):
    """Click handler for the menu window; toggle rules cells."""
    cell = rules_overlay_cell_at(x, y)
    if cell is not None:
        c1, c2 = cell
        cycle_rule_for_cell(c1, c2)
    # no need to close menu here


def random_velocity_for_color(color_key: str) -> VelocityVector:
    if color_key == "r":
        speed = random.uniform(2.5, 4.0)
    elif color_key == "y":
        speed = random.uniform(2.0, 3.0)
    elif color_key == "g":
        speed = random.uniform(1.5, 2.5)
    else:
        speed = random.uniform(0.8, 1.5)
    angle = random.uniform(0, 2 * math.pi)
    return VelocityVector(speed * math.cos(angle), speed * math.sin(angle))


def random_empty_position(radius: float, max_attempts: int = 200) -> Optional[Tuple[float, float]]:
    half_w, half_h = SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2
    for _ in range(max_attempts):
        x = random.uniform(-half_w + radius, half_w - radius)
        y = random.uniform(-half_h + radius, half_h - radius)
        ok = True
        for s in SHAPES:
            if math.hypot(x - s.x, y - s.y) < (radius + s.bounding_radius() + 3):
                ok = False
                break
        if ok:
            return x, y
    return None


def bounding_radius_for_color(color_key: str) -> float:
    if color_key == "r":
        return 22 * 1.5
    if color_key == "g":
        return 26 * 1.1
    if color_key == "b":
        return (30 * math.sqrt(2)) / 2
    if color_key == "y":
        return 26
    return 22 * 1.5


def spawn_key(color_key: str):
    r = bounding_radius_for_color(color_key)
    pos = random_empty_position(r)
    if pos is None:
        return
    x, y = pos
    SHAPES.append(shape_for_color(color_key, x, y))


def draw_rules_overlay_on_t(t):
    left, top, cell, rows, cols = rules_overlay_geometry()
    t.up()
    t.color("#CCCCCC")
    t.goto(left, top + 20)
    t.write(
        "Collision Rules (click to cycle)", align="left", font=("Arial", 12, "bold")
    )
    for ri, c1 in enumerate(COLORS_ORDER):
        for ci, c2 in enumerate(COLORS_ORDER):
            x0 = left + ci * cell
            y0 = top - ri * cell
            t.goto(x0, y0)
            t.color("#888888")
            t.down()
            for _ in range(2):
                t.forward(cell)
                t.right(90)
                t.forward(cell)
                t.right(90)
            t.up()
            rule = COLLISION_RULES[(min(c1, c2), max(c1, c2))]
            t.color("white")
            t.goto(x0 + 6, y0 - 20)
            t.write(f"{c1.upper()} x {c2.upper()}\n{rule}", align="left", font=("Arial", 10, "normal"))


def rules_overlay_geometry():
    grid_cell = 110
    cols = len(COLORS_ORDER)
    rows = len(COLORS_ORDER)
    total_w = cols * grid_cell
    total_h = rows * grid_cell
    left = - (total_w / 2)
    top = total_h / 2
    return left, top, grid_cell, rows, cols


def rules_overlay_cell_at(x: float, y: float) -> Optional[Tuple[str, str]]:
    left, top, cell, rows, cols = rules_overlay_geometry()
    if not (left <= x <= left + cols * cell and top - rows * cell <= y <= top):
        return None
    ci = int((x - left) // cell)
    ri = int((top - y) // cell)
    c1 = COLORS_ORDER[ri]
    c2 = COLORS_ORDER[ci]
    return c1, c2


def convert_shape(shape: "Polygon", target_color_key: str) -> "Polygon":
    new_shape = shape_for_color(target_color_key, shape.x, shape.y)
    new_shape.velocity = shape.velocity
    new_shape.show_circle = shape.show_circle
    return new_shape


def handle_collisions():
    n = len(SHAPES)
    to_remove: set[int] = set()
    to_replace: List[Tuple[int, Polygon]] = []

    for i in range(n):
        if i in to_remove:
            continue
        a = SHAPES[i]
        for j in range(i + 1, n):
            if j in to_remove:
                continue
            b = SHAPES[j]
            ra = a.bounding_radius()
            rb = b.bounding_radius()
            dx = b.x - a.x
            dy = b.y - a.y
            dist = math.hypot(dx, dy)
            if dist == 0:
                dist = 1e-6
                dx, dy = 1e-6, 0.0
            if dist <= ra + rb:
                # They collide
                # Simple explosion rule: randomly pick one to remove
                # Or you can apply color rules first
                # Here: remove either a or b at random
                victim = random.choice([i, j])
                to_remove.add(victim)
                # If you want to convert instead of remove, use to_replace logic
                # (not doing here)
                break  # break inner loop; i may be removed
    if to_replace:
        for idx, new_shape in to_replace:
            if idx not in to_remove and 0 <= idx < len(SHAPES):
                SHAPES[idx] = new_shape
    if to_remove:
        # Remove from highest index downward so list indices stay valid
        for idx in sorted(to_remove, reverse=True):
            if 0 <= idx < len(SHAPES):
                del SHAPES[idx]


def setup_simulation():
    screen = turtle.Screen()
    screen.setup(SCREEN_WIDTH + 50, SCREEN_HEIGHT + 50)
    screen.title("Polygon Billiards")
    screen.bgcolor("#1a202c")
    screen.tracer(0)

    t = turtle.Turtle()
    t.hideturtle()
    t.speed(0)

    global HUD_TURTLE
    HUD_TURTLE = turtle.Turtle()
    HUD_TURTLE.hideturtle()
    HUD_TURTLE.speed(0)

    for color_key, count in INITIAL_COUNTS.items():
        for _ in range(count):
            tmp = shape_for_color(color_key, 0, 0)
            r = tmp.bounding_radius()
            pos = random_empty_position(r)
            if pos is None:
                continue
            x, y = pos
            SHAPES.append(shape_for_color(color_key, x, y))

    screen.onclick(handle_click_main)
    screen.listen()
    screen.onkey(lambda: spawn_key("b"), "b")
    screen.onkey(lambda: spawn_key("g"), "g")
    screen.onkey(lambda: spawn_key("r"), "r")
    screen.onkey(lambda: spawn_key("y"), "y")
    screen.onkey(screen.bye, "q")

    return screen, t


def setup_menu_window():
    """Separate window (tab) for rules/menu."""
    menu = turtle.Screen()
    menu.title("Rules / Menu")
    menu.setup(500, 500)
    menu.tracer(0)

    mt = turtle.Turtle()
    mt.hideturtle()
    mt.speed(0)

    menu.onclick(handle_click_menu)
    return menu, mt


def animate(screen, t, menu, mt):
    t.clear()
    if HUD_TURTLE:
        HUD_TURTLE.clear()

    for shape in SHAPES:
        shape.move(CANVAS)

    handle_collisions()

    for shape in SHAPES:
        shape.draw(t)

    draw_hud()
    screen.update()

    # Draw rules in menu window
    mt.clear()
    draw_rules_overlay_on_t(mt)
    menu.update()

    screen.ontimer(lambda: animate(screen, t, menu, mt), ANIMATION_DELAY_MS)


def draw_hud():
    if HUD_TURTLE is None:
        return
    HUD_TURTLE.up()
    HUD_TURTLE.color("white")
    HUD_TURTLE.goto(-SCREEN_WIDTH / 2 + 10, SCREEN_HEIGHT / 2 - 30)
    HUD_TURTLE.write(
        f"Mass mode: {MASS_MODE}   Shapes: {len(SHAPES)}   (q) quit",
        align="left",
        font=("Arial", 12, "normal"),
    )


def shape_for_color(color_key: str, x: float, y: float) -> Polygon:
    if color_key == "r":
        return Triangle(x, y)
    if color_key == "g":
        return Pentagon(x, y)
    if color_key == "b":
        return Square(x, y)
    if color_key == "y":
        return Hexagon(x, y)
    return Triangle(x, y)


if __name__ == "__main__":
    screen, t = setup_simulation()
    menu, mt = setup_menu_window()
    animate(screen, t, menu, mt)
    screen.mainloop()
    menu.mainloop()

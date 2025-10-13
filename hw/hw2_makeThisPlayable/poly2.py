import turtle
import math
import random
from abc import ABC, abstractmethod
from typing import Dict, Tuple, List, Optional

# Global constants for the screen/canvas boundaries
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SHAPES: List["Polygon"] = []  # Global list to hold all Polygon objects
ANIMATION_DELAY_MS = 20  # 50 frames per second (1000ms / 50 = 20ms)

# --- GAME CONSTANTS & STATE ---

# Colors keyed by single letter
COLOR_HEX: Dict[str, str] = {
    "r": "#FF3B30",  # Red
    "g": "#34C759",  # Green
    "b": "#1E90FF",  # Blue
    "y": "#FFCC00",  # Yellow
}

# Initial counts per color
INITIAL_COUNTS: Dict[str, int] = {"r": 5, "g": 5, "b": 5, "y": 5}

# Mass mode: "equal" or "area"
MASS_MODE: str = "equal"

# Overlay state for rules table
RULES_OVERLAY_ACTIVE: bool = False

# Drawing helpers (initialized in setup)
HUD_TURTLE: Optional[turtle.Turtle] = None

# Collision rule outcomes. Mapping of (c1, c2) -> rule string
# Rules are symmetric by default; we store with sorted color pair
# Possible rules:
# - "noop" (no color change)
# - "both_disappear", "a_disappear", "b_disappear"
# - "a->r", "a->g", "a->b", "a->y"
# - "b->r", "b->g", "b->b", "b->y"
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

# --- UTILITY FUNCTIONS ---


def draw_dashed_circle(t, x, y, radius):
    """Draws a dashed circle outline using turtle segments."""
    t.up()
    t.goto(x, y - radius)  # Move to the bottom point of the circle

    t.color("gray")
    t.pensize(1)

    # Calculate how many segments we need for the dash pattern
    segments = 30
    segment_angle = 360 / segments

    t.setheading(0)  # Reset heading

    for i in range(segments):
        # Even segments draw the dash, odd segments are the gap
        if i % 2 == 0:
            t.down()
        else:
            t.up()

        # Draw a small arc segment
        t.circle(radius, segment_angle)
    t.up()


# --- 1. Utility Classes & Concepts (Exercises 6, 7, 8) ---


class VelocityVector:
    """Represents the movement vector of a polygon."""

    def __init__(self, vx, vy):
        self.vx = vx
        self.vy = vy

    # Operator Overloading for addition (+)
    def __add__(self, other):
        if isinstance(other, VelocityVector):
            return VelocityVector(self.vx + other.vx, self.vy + other.vy)
        return NotImplemented

    def __repr__(self):
        return f"VelocityVector(vx={self.vx:.2f}, vy={self.vy:.2f})"

    @property
    def speed(self) -> float:
        return math.hypot(self.vx, self.vy)


class CanvasHost:
    """Represents the environment boundaries."""

    def __init__(self, width, height):
        self.width = width
        self.height = height  # FIX: was incorrectly set to width

    @property
    def dimensions(self):
        return {"w": self.width, "h": self.height}


# Initialize the Canvas Object
CANVAS = CanvasHost(SCREEN_WIDTH, SCREEN_HEIGHT)


# --- 2. Abstract Base Class (ABC): Polygon ---


class Polygon(ABC):
    """Abstract Base Class that defines the contract for all shape objects."""

    active_count = 0
    # NEW: Default value; each instance may toggle its own circle
    DRAW_BOUNDING_CIRCLE = True

    def __init__(self, x, y, edges, size, color):
        self.x = x
        self.y = y
        self.edges = edges
        self._size = size
        self.color = color
        self.color_key = "r"  # default; subclass adjusts

        speed = random.uniform(1, 3)
        angle = random.uniform(0, 2 * math.pi)
        self.velocity = VelocityVector(
            vx=speed * math.cos(angle), vy=speed * math.sin(angle)
        )

        Polygon.active_count += 1
        # Instance-level toggle for bounding circle visibility
        self.show_circle = Polygon.DRAW_BOUNDING_CIRCLE

    def __del__(self):
        Polygon.active_count -= 1

    @property
    def size(self):
        """Getter for size."""
        return self._size

    @size.setter
    def size(self, new_size):
        """Setter for size with validation (Exercise 8)."""
        if new_size > 0:
            self._size = new_size
        else:
            raise ValueError("Polygon size must be positive.")

    def update_position(self):
        """Updates the position based on the current velocity."""
        self.x += self.velocity.vx
        self.y += self.velocity.vy

    @abstractmethod
    def bounding_radius(self) -> float:
        """Returns the circumcircle radius for collisions and toggling."""
        raise NotImplementedError

    def mass(self) -> float:
        if MASS_MODE == "equal":
            return 1.0
        # approximate regular n-gon area using circumradius
        R = self.bounding_radius()
        area = 0.5 * self.edges * (R ** 2) * math.sin(2 * math.pi / self.edges)
        return max(0.1, area / 100.0)

    @abstractmethod
    def draw(self, t):
        """Defines how the shape is drawn on the turtle canvas."""

    @abstractmethod
    def move(self, canvas):
        """Defines the unique boundary logic (bounce or wrap)."""
        pass


# --- 3. Concrete Subclasses: Implementing Polymorphism ---


class Triangle(Polygon):
    """Odd-sided shape: Bounces off walls."""

    def __init__(self, x, y):
        super().__init__(x, y, 3, 22, COLOR_HEX["r"])  # Red
        self.color_key = "r"
        self.velocity = random_velocity_for_color(self.color_key)

    # Method Overriding: Draw implementation using turtle
    def draw(self, t):
        # Draw circumcircle if toggled
        if self.show_circle:
            # Use radius slightly larger than the inscribed size for visibility
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
        s = self.bounding_radius()  # Use bounding radius for collision check

        if self.x + s > w or self.x - s < -w:
            self.velocity.vx *= -1
            self.x = max(-w + s, min(self.x, w - s))

        if self.y + s > h or self.y - s < -h:
            self.velocity.vy *= -1
            self.y = max(-h + s, min(self.y, h - s))

    def bounding_radius(self) -> float:
        return self.size * 1.5


class Square(Polygon):
    """Even-sided shape: Wraps around the screen."""

    def __init__(self, x, y):
        super().__init__(x, y, 4, 30, COLOR_HEX["b"])  # Blue
        self.color_key = "b"
        self.velocity = random_velocity_for_color(self.color_key)

    # Method Overriding: Draw implementation
    def draw(self, t):
        # Draw circumcircle if toggled
        if self.show_circle:
            # Radius is half the diagonal for a snug fit
            draw_dashed_circle(t, self.x, self.y, self.bounding_radius())

        t.up()
        t.goto(
            self.x - self.size / 2, self.y - self.size / 2
        )  # Start bottom-left corner
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

    def bounding_radius(self) -> float:
        # Half diagonal of square
        return (self.size * math.sqrt(2)) / 2


class Pentagon(Polygon):
    """Odd-sided shape: Bounces off walls (reusing Triangle logic)."""

    def __init__(self, x, y):
        super().__init__(x, y, 5, 26, COLOR_HEX["g"])  # Green
        self.color_key = "g"
        self.velocity = random_velocity_for_color(self.color_key)

    # Method Overriding: Draw implementation
    def draw(self, t):
        # Draw circumcircle if toggled
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

    def bounding_radius(self) -> float:
        return self.size * 1.1


class Hexagon(Polygon):
    """Even-sided shape: Wraps around the screen (reusing Square logic)."""

    def __init__(self, x, y):
        super().__init__(x, y, 6, 26, COLOR_HEX["y"])  # Yellow
        self.color_key = "y"
        self.velocity = random_velocity_for_color(self.color_key)

    # Method Overriding: Draw implementation
    def draw(self, t):
        # Draw circumcircle if toggled
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

    def bounding_radius(self) -> float:
        # For a regular hexagon, circumradius equals side length
        return self.size


# --- 4. Simulation Control ---


def cycle_rule_for_cell(c1: str, c2: str):
    key = (min(c1, c2), max(c1, c2))
    current = COLLISION_RULES.get(key, "noop")
    idx = (RULE_OPTIONS.index(current) + 1) % len(RULE_OPTIONS)
    COLLISION_RULES[key] = RULE_OPTIONS[idx]


def handle_click(x, y):
    """Toggle per-shape circle if click inside its circumcircle; edit rules if overlay active."""
    global RULES_OVERLAY_ACTIVE

    if RULES_OVERLAY_ACTIVE:
        cell = rules_overlay_cell_at(x, y)
        if cell is not None:
            c1, c2 = cell
            cycle_rule_for_cell(c1, c2)
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


# --- Helpers: physics, HUD, overlay, and controls ---

def toggle_mass_mode():
    global MASS_MODE
    MASS_MODE = "area" if MASS_MODE == "equal" else "equal"


def draw_hud():
    if HUD_TURTLE is None:
        return
    HUD_TURTLE.up()
    HUD_TURTLE.color("white")
    HUD_TURTLE.goto(-SCREEN_WIDTH / 2 + 10, SCREEN_HEIGHT / 2 - 30)
    HUD_TURTLE.write(
        f"Mass mode: {MASS_MODE}   Shapes: {len(SHAPES)}   (m) toggle, (e) edit rules, (q) quit",
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


def draw_rules_overlay():
    if HUD_TURTLE is None:
        return
    left, top, cell, rows, cols = rules_overlay_geometry()
    HUD_TURTLE.up()
    HUD_TURTLE.color("#CCCCCC")
    HUD_TURTLE.goto(left, top + 20)
    HUD_TURTLE.write(
        "Collision Rules (click cell to cycle; 'e' to close)",
        align="left",
        font=("Arial", 12, "bold"),
    )

    for ri, c1 in enumerate(COLORS_ORDER):
        for ci, c2 in enumerate(COLORS_ORDER):
            x0 = left + ci * cell
            y0 = top - ri * cell
            HUD_TURTLE.goto(x0, y0)
            HUD_TURTLE.color("#888888")
            HUD_TURTLE.down()
            for _ in range(2):
                HUD_TURTLE.forward(cell)
                HUD_TURTLE.right(90)
                HUD_TURTLE.forward(cell)
                HUD_TURTLE.right(90)
            HUD_TURTLE.up()
            rule = COLLISION_RULES[(min(c1, c2), max(c1, c2))]
            HUD_TURTLE.color("white")
            HUD_TURTLE.goto(x0 + 6, y0 - 20)
            HUD_TURTLE.write(
                f"{c1.upper()} x {c2.upper()}\n{rule}",
                align="left",
                font=("Arial", 10, "normal"),
            )


def rules_overlay_geometry():
    grid_cell = 110
    cols = len(COLORS_ORDER)
    rows = len(COLORS_ORDER)
    total_w = cols * grid_cell
    total_h = rows * grid_cell
    left = SCREEN_WIDTH / 2 - total_w - 10
    top = SCREEN_HEIGHT / 2 - 50
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


def toggle_rules_overlay():
    global RULES_OVERLAY_ACTIVE
    RULES_OVERLAY_ACTIVE = not RULES_OVERLAY_ACTIVE


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
                nx, ny = dx / dist, dy / dist
                rvx = b.velocity.vx - a.velocity.vx
                rvy = b.velocity.vy - a.velocity.vy
                rel_vel_along_normal = rvx * nx + rvy * ny
                if rel_vel_along_normal < 0:
                    overlap = (ra + rb) - dist
                    if overlap > 0:
                        push_a = overlap * 0.5
                        push_b = overlap - push_a
                        a.x -= nx * push_a
                        a.y -= ny * push_a
                        b.x += nx * push_b
                        b.y += ny * push_b

                    m1 = a.mass()
                    m2 = b.mass()
                    v1n = a.velocity.vx * nx + a.velocity.vy * ny
                    v2n = b.velocity.vx * nx + b.velocity.vy * ny
                    v1t_x = a.velocity.vx - v1n * nx
                    v1t_y = a.velocity.vy - v1n * ny
                    v2t_x = b.velocity.vx - v2n * nx
                    v2t_y = b.velocity.vy - v2n * ny
                    v1n_prime = (v1n * (m1 - m2) + 2 * m2 * v2n) / (m1 + m2)
                    v2n_prime = (v2n * (m2 - m1) + 2 * m1 * v1n) / (m1 + m2)
                    a.velocity.vx = v1t_x + v1n_prime * nx
                    a.velocity.vy = v1t_y + v1n_prime * ny
                    b.velocity.vx = v2t_x + v2n_prime * nx
                    b.velocity.vy = v2t_y + v2n_prime * ny

                    rule_key = (min(a.color_key, b.color_key), max(a.color_key, b.color_key))
                    rule = COLLISION_RULES.get(rule_key, "noop")
                    if rule == "both_disappear":
                        to_remove.add(i)
                        to_remove.add(j)
                    elif rule == "a_disappear":
                        to_remove.add(i)
                    elif rule == "b_disappear":
                        to_remove.add(j)
                    elif rule.startswith("a->"):
                        new_c = rule.split("->", 1)[1]
                        to_replace.append((i, convert_shape(a, new_c)))
                    elif rule.startswith("b->"):
                        new_c = rule.split("->", 1)[1]
                        to_replace.append((j, convert_shape(b, new_c)))

    if to_remove or to_replace:
        for idx, new_shape in to_replace:
            if idx not in to_remove and 0 <= idx < len(SHAPES):
                SHAPES[idx] = new_shape
        for idx in sorted(to_remove, reverse=True):
            if 0 <= idx < len(SHAPES):
                del SHAPES[idx]

def setup_simulation():
    """Initializes the turtle screen and creates the shapes."""

    # 1. Setup the Screen
    screen = turtle.Screen()
    screen.setup(SCREEN_WIDTH + 50, SCREEN_HEIGHT + 50)
    screen.title("Polygon Billiards with Rules (press 'e' to edit rules)")
    screen.bgcolor("#1a202c")  # Dark background
    screen.tracer(0)  # Turn off screen updates for smooth animation

    # 2. Setup the Turtle drawer object (t)
    t = turtle.Turtle()
    t.hideturtle()
    t.speed(0)  # Fastest drawing speed

    # HUD turtle for overlays/text
    global HUD_TURTLE
    HUD_TURTLE = turtle.Turtle()
    HUD_TURTLE.hideturtle()
    HUD_TURTLE.speed(0)

    # 3. Create the shapes: fixed counts per color, placed non-overlapping
    for color_key, count in INITIAL_COUNTS.items():
        for _ in range(count):
            temp = shape_for_color(color_key, 0, 0)
            r = temp.bounding_radius()
            pos = random_empty_position(r)
            if pos is None:
                continue
            x, y = pos
            SHAPES.append(shape_for_color(color_key, x, y))

    print(f"Total polygons initialized: {Polygon.active_count}")

    # 4. Bind click and keys
    screen.onclick(handle_click)
    screen.listen()
    screen.onkey(toggle_mass_mode, "m")
    screen.onkey(lambda: spawn_key("b"), "b")
    screen.onkey(lambda: spawn_key("g"), "g")
    screen.onkey(lambda: spawn_key("r"), "r")
    screen.onkey(lambda: spawn_key("y"), "y")
    screen.onkey(toggle_rules_overlay, "e")
    screen.onkey(screen.bye, "q")

    return screen, t


def animate(screen, t):
    """The main simulation loop."""

    t.clear()
    if HUD_TURTLE:
        HUD_TURTLE.clear()

    # Move shapes
    for shape in SHAPES:
        shape.move(CANVAS)

    # Handle collisions and color rules
    handle_collisions()

    # Draw shapes
    for shape in SHAPES:
        shape.draw(t)

    # HUD and overlays
    draw_hud()
    if RULES_OVERLAY_ACTIVE:
        draw_rules_overlay()

    screen.update()

    screen.ontimer(lambda: animate(screen, t), ANIMATION_DELAY_MS)


if __name__ == "__main__":
    try:
        screen, t = setup_simulation()

        # Start the animation loop
        animate(screen, t)

        screen.mainloop()

    except Exception as e:
        print(f"An error occurred during simulation: {e}")


# --- New functions added for physics, HUD, overlay, and controls ---

def toggle_mass_mode():
    global MASS_MODE
    MASS_MODE = "area" if MASS_MODE == "equal" else "equal"


def draw_hud():
    if HUD_TURTLE is None:
        return
    HUD_TURTLE.up()
    HUD_TURTLE.color("white")
    HUD_TURTLE.goto(-SCREEN_WIDTH / 2 + 10, SCREEN_HEIGHT / 2 - 30)
    HUD_TURTLE.write(
        f"Mass mode: {MASS_MODE}   Shapes: {len(SHAPES)}   (m) toggle, (e) edit rules, (q) quit",
        align="left",
        font=("Arial", 12, "normal"),
    )


 

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


def draw_rules_overlay():
    if HUD_TURTLE is None:
        return
    left, top, cell, rows, cols = rules_overlay_geometry()
    HUD_TURTLE.up()
    HUD_TURTLE.color("#CCCCCC")
    HUD_TURTLE.goto(left, top + 20)
    HUD_TURTLE.write(
        "Collision Rules (click cell to cycle; 'e' to close)",
        align="left",
        font=("Arial", 12, "bold"),
    )

    for ri, c1 in enumerate(COLORS_ORDER):
        for ci, c2 in enumerate(COLORS_ORDER):
            x0 = left + ci * cell
            y0 = top - ri * cell
            HUD_TURTLE.goto(x0, y0)
            HUD_TURTLE.color("#888888")
            HUD_TURTLE.down()
            for _ in range(2):
                HUD_TURTLE.forward(cell)
                HUD_TURTLE.right(90)
                HUD_TURTLE.forward(cell)
                HUD_TURTLE.right(90)
            HUD_TURTLE.up()
            rule = COLLISION_RULES[(min(c1, c2), max(c1, c2))]
            HUD_TURTLE.color("white")
            HUD_TURTLE.goto(x0 + 6, y0 - 20)
            HUD_TURTLE.write(
                f"{c1.upper()} x {c2.upper()}\n{rule}",
                align="left",
                font=("Arial", 10, "normal"),
            )


def rules_overlay_geometry():
    grid_cell = 110
    cols = len(COLORS_ORDER)
    rows = len(COLORS_ORDER)
    total_w = cols * grid_cell
    total_h = rows * grid_cell
    left = SCREEN_WIDTH / 2 - total_w - 10
    top = SCREEN_HEIGHT / 2 - 50
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


def toggle_rules_overlay():
    global RULES_OVERLAY_ACTIVE
    RULES_OVERLAY_ACTIVE = not RULES_OVERLAY_ACTIVE


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
                nx, ny = dx / dist, dy / dist
                rvx = b.velocity.vx - a.velocity.vx
                rvy = b.velocity.vy - a.velocity.vy
                rel_vel_along_normal = rvx * nx + rvy * ny
                if rel_vel_along_normal < 0:
                    overlap = (ra + rb) - dist
                    if overlap > 0:
                        push_a = overlap * 0.5
                        push_b = overlap - push_a
                        a.x -= nx * push_a
                        a.y -= ny * push_a
                        b.x += nx * push_b
                        b.y += ny * push_b

                    m1 = a.mass()
                    m2 = b.mass()
                    v1n = a.velocity.vx * nx + a.velocity.vy * ny
                    v2n = b.velocity.vx * nx + b.velocity.vy * ny
                    v1t_x = a.velocity.vx - v1n * nx
                    v1t_y = a.velocity.vy - v1n * ny
                    v2t_x = b.velocity.vx - v2n * nx
                    v2t_y = b.velocity.vy - v2n * ny
                    v1n_prime = (v1n * (m1 - m2) + 2 * m2 * v2n) / (m1 + m2)
                    v2n_prime = (v2n * (m2 - m1) + 2 * m1 * v1n) / (m1 + m2)
                    a.velocity.vx = v1t_x + v1n_prime * nx
                    a.velocity.vy = v1t_y + v1n_prime * ny
                    b.velocity.vx = v2t_x + v2n_prime * nx
                    b.velocity.vy = v2t_y + v2n_prime * ny

                    rule_key = (min(a.color_key, b.color_key), max(a.color_key, b.color_key))
                    rule = COLLISION_RULES.get(rule_key, "noop")
                    if rule == "both_disappear":
                        to_remove.add(i)
                        to_remove.add(j)
                    elif rule == "a_disappear":
                        to_remove.add(i)
                    elif rule == "b_disappear":
                        to_remove.add(j)
                    elif rule.startswith("a->"):
                        new_c = rule.split("->", 1)[1]
                        to_replace.append((i, convert_shape(a, new_c)))
                    elif rule.startswith("b->"):
                        new_c = rule.split("->", 1)[1]
                        to_replace.append((j, convert_shape(b, new_c)))

    if to_remove or to_replace:
        for idx, new_shape in to_replace:
            if idx not in to_remove and 0 <= idx < len(SHAPES):
                SHAPES[idx] = new_shape
        for idx in sorted(to_remove, reverse=True):
            if 0 <= idx < len(SHAPES):
                del SHAPES[idx]
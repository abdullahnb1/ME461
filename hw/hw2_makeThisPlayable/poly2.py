import turtle
import math
import random
from abc import ABC, abstractmethod

# Global constants for the screen/canvas boundaries
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SHAPES = []  # Global list to hold all Polygon objects
ANIMATION_DELAY_MS = 20  # 50 frames per second (1000ms / 50 = 20ms)

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
    # NEW: Class attribute to control drawing of bounding circles globally
    DRAW_BOUNDING_CIRCLE = True

    def __init__(self, x, y, edges, size, color):
        self.x = x
        self.y = y
        self.edges = edges
        self._size = size
        self.color = color

        speed = random.uniform(1, 3)
        angle = random.uniform(0, 2 * math.pi)
        self.velocity = VelocityVector(
            vx=speed * math.cos(angle), vy=speed * math.sin(angle)
        )

        Polygon.active_count += 1

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
        super().__init__(x, y, 3, 20, "#FF4500")  # Orange

    # Method Overriding: Draw implementation using turtle
    def draw(self, t):
        # Check the class attribute before drawing the circle
        if Polygon.DRAW_BOUNDING_CIRCLE:
            # Use radius slightly larger than the inscribed size for visibility
            draw_dashed_circle(t, self.x, self.y, self.size * 1.5)

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
        s = self.size * 1.5  # Use bounding radius for collision check

        if self.x + s > w or self.x - s < -w:
            self.velocity.vx *= -1
            self.x = max(-w + s, min(self.x, w - s))

        if self.y + s > h or self.y - s < -h:
            self.velocity.vy *= -1
            self.y = max(-h + s, min(self.y, h - s))


class Square(Polygon):
    """Even-sided shape: Wraps around the screen."""

    def __init__(self, x, y):
        super().__init__(x, y, 4, 30, "#1E90FF")  # Blue

    # Method Overriding: Draw implementation
    def draw(self, t):
        # Check the class attribute before drawing the circle
        if Polygon.DRAW_BOUNDING_CIRCLE:
            # Radius is half the diagonal for a snug fit
            draw_dashed_circle(t, self.x, self.y, self.size * 0.75)

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


class Pentagon(Polygon):
    """Odd-sided shape: Bounces off walls (reusing Triangle logic)."""

    def __init__(self, x, y):
        super().__init__(x, y, 5, 25, "#3CB371")  # Green

    # Method Overriding: Draw implementation
    def draw(self, t):
        # Check the class attribute before drawing the circle
        if Polygon.DRAW_BOUNDING_CIRCLE:
            draw_dashed_circle(t, self.x, self.y, self.size * 1.1)

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
        s = self.size * 1.1

        if self.x + s > w or self.x - s < -w:
            self.velocity.vx *= -1
            self.x = max(-w + s, min(self.x, w - s))

        if self.y + s > h or self.y - s < -h:
            self.velocity.vy *= -1
            self.y = max(-h + s, min(self.y, h - s))


class Hexagon(Polygon):
    """Even-sided shape: Wraps around the screen (reusing Square logic)."""

    def __init__(self, x, y):
        super().__init__(x, y, 6, 25, "#DAA520")  # Gold

    # Method Overriding: Draw implementation
    def draw(self, t):
        # Check the class attribute before drawing the circle
        if Polygon.DRAW_BOUNDING_CIRCLE:
            draw_dashed_circle(t, self.x, self.y, self.size * 1.05)

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


# --- 4. Simulation Control ---


def toggle_circles(x, y):
    """Toggles the visibility of the dashed bounding circles."""
    # Toggle the class attribute
    Polygon.DRAW_BOUNDING_CIRCLE = not Polygon.DRAW_BOUNDING_CIRCLE
    status = "ON" if Polygon.DRAW_BOUNDING_CIRCLE else "OFF"
    # Print status to the console for feedback
    print(f"Bounding circles Toggled: {status}")


def setup_simulation():
    """Initializes the turtle screen and creates the shapes."""

    # 1. Setup the Screen
    screen = turtle.Screen()
    screen.setup(SCREEN_WIDTH + 50, SCREEN_HEIGHT + 50)
    screen.title("OOP Polygon Simulation (Python ABC Demo)")
    screen.bgcolor("#1a202c")  # Dark background
    screen.tracer(0)  # Turn off screen updates for smooth animation

    # 2. Setup the Turtle drawer object (t)
    t = turtle.Turtle()
    t.hideturtle()
    t.speed(0)  # Fastest drawing speed

    # 3. Create the shapes
    shape_types = [Triangle, Square, Pentagon, Hexagon]

    for _ in range(20):
        ShapeClass = random.choice(shape_types)

        # Random start position within boundaries
        x = random.uniform(-SCREEN_WIDTH / 2 + 50, SCREEN_WIDTH / 2 - 50)
        y = random.uniform(-SCREEN_HEIGHT / 2 + 50, SCREEN_HEIGHT / 2 - 50)

        SHAPES.append(ShapeClass(x, y))

    print(f"Total polygons initialized: {Polygon.active_count}")

    # 4. Bind the toggle function to the screen click event
    screen.onclick(toggle_circles)

    return screen, t


def animate(screen, t):
    """The main simulation loop."""

    t.clear()

    for shape in SHAPES:
        shape.move(CANVAS)
        shape.draw(t)

    screen.update()

    screen.ontimer(lambda: animate(screen, t), ANIMATION_DELAY_MS)


if __name__ == "__main__":
    try:
        screen, t = setup_simulation()

        # Start the animation loop
        animate(screen, t)

        # Uncomment this to test Exercise 9:
        # try:
        #     base_polygon = Polygon(0, 0, 4, 10, 'red')
        # except TypeError as e:
        #     print(f"\nSUCCESS: Caught expected TypeError for ABC instantiation: {e}")

        screen.mainloop()

    except Exception as e:
        print(f"An error occurred during simulation: {e}")
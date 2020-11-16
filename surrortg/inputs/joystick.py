import logging
import math
from enum import Enum, auto
from . import Input


class Directions(Enum):
    """Emun for Joystick.get_direction_8() and get_direction_4() results
    """

    MIDDLE = auto()
    TOP = auto()
    BOTTOM = auto()
    LEFT = auto()
    RIGHT = auto()
    TOP_LEFT = auto()
    TOP_RIGHT = auto()
    BOTTOM_LEFT = auto()
    BOTTOM_RIGHT = auto()


ONE_16TH = math.pi / 8
ONE_8TH = math.pi / 4
DIRECTION_DICT_8 = {
    8: Directions.LEFT,
    7: Directions.LEFT,
    6: Directions.TOP_LEFT,
    5: Directions.TOP_LEFT,
    4: Directions.TOP,
    3: Directions.TOP,
    2: Directions.TOP_RIGHT,
    1: Directions.TOP_RIGHT,
    0: Directions.RIGHT,
    -1: Directions.BOTTOM_RIGHT,
    -2: Directions.BOTTOM_RIGHT,
    -3: Directions.BOTTOM,
    -4: Directions.BOTTOM,
    -5: Directions.BOTTOM_LEFT,
    -6: Directions.BOTTOM_LEFT,
    -7: Directions.LEFT,
    -8: Directions.LEFT,
}
DIRECTION_DICT_4 = {
    4: Directions.LEFT,
    3: Directions.LEFT,
    2: Directions.TOP,
    1: Directions.TOP,
    0: Directions.RIGHT,
    -1: Directions.BOTTOM,
    -2: Directions.BOTTOM,
    -3: Directions.LEFT,
    -4: Directions.LEFT,
}


class Joystick(Input):
    """Joystick input class

    Implement custom logic based on directions and amounts or x/y coordinates.

    :param min_amount: if input amount is less than this middle() is
        called, defaults to 0.1
    :type min_amount: float, optional
    """

    def __init__(self, min_amount=0.1):
        assert isinstance(
            min_amount, (float, int)
        ), "min_amount must be float or int"

        self._min_amount = min_amount

    async def _on_input(self, command, seat):
        """Joystick input functionality

        Parses x- and y-coordinates and calls handle_coordinates
        :param command: Command from game engine
        :type command: dict
        :param seat: Robot seat
        :type seat: int
        """
        x = self._parse_coordinate(command, "x")
        y = self._parse_coordinate(command, "y")
        if x is not None and y is not None:
            await self.handle_coordinates(x, y, seat)

    def _parse_coordinate(self, command, key):
        """Parse the coordinate given as key from the command

        Returns the parsed coordinate or None if command is invalid
        :param command: Command from game engine
        :type command: dict
        :param key: coordinate key name
        :type key: str
        :return: key coordinate parsed from command
        :rtype: float or None
        """
        if key not in command:
            logging.warning("Joystick: invalid command received")
            return None

        try:
            val = float(command[key])
        except (ValueError, TypeError):
            logging.warning(
                f"Joystick: could not convert {command[key]} into float"
            )
            return None

        if val < -1.0 or val > 1.0:
            logging.warning(f"Joystick: out of range value {val} received")
            return None

        return val

    async def handle_coordinates(self, x, y, seat):
        """Coordinate based Joystick control

        Middle position means x=0, y=0. Right means x is positive, left means
        x is negative. Top means y is positive, bottom means y is negative.

        :param x: x-coordinate, between -1.0 and 1.0
        :type x: float
        :param y: y-coordinate, between -1.0 and 1.0
        :type y: float
        :param seat: Robot seat
        :type seat: int
        """
        pass

    def get_direction_8(self, x, y):
        """Get the current direction from 8 main directions + middle

        Result Directions.MIDDLE means that Joystick distance from the center
        point is less than self.min_amount.

        Other possible results: Directions.TOP, BOTTOM, LEFT, RIGHT, TOP_LEFT,
        TOP_RIGHT, BOTTOM_LEFT, BOTTOM_RIGHT.

        :param x: x-coordinate, between -1.0 and 1.0
        :type x: float
        :param y: y-coordinate, between -1.0 and 1.0
        :type y: float
        :return: Current direction
        :rtype: Directions
        """
        direction, amount = self.get_direction_and_amount(x, y)
        if amount < self._min_amount:
            return Directions.MIDDLE
        else:
            key = int(direction / ONE_16TH)
            return DIRECTION_DICT_8[key]

    def get_direction_4(self, x, y):
        """Get the current direction from 4 main directions + middle

        Result Directions.MIDDLE means that Joystick distance from the center
        point is less than self.min_amount.

        Other possible results: Directions.TOP, BOTTOM, LEFT, RIGHT.

        :param x: x-coordinate, between -1.0 and 1.0
        :type x: float
        :param y: y-coordinate, between -1.0 and 1.0
        :type y: float
        :return: Current direction
        :rtype: Directions
        """
        direction, amount = self.get_direction_and_amount(x, y)
        if amount < self._min_amount:
            return Directions.MIDDLE
        else:
            key = int(direction / ONE_8TH)
            return DIRECTION_DICT_4[key]

    def get_direction_and_amount(self, x, y):
        """Get exact direction and amount from the x/y coordinates

        This method is good when neither get_direction_8 or get_direction_4
        are not accurate enough.

        :param x: x-coordinate, between -1.0 and 1.0
        :type x: float
        :param y: y-coordinate, between -1.0 and 1.0
        :type y: float
        :return: direction and amount in radians, from -pi to +pi
        :rtype: (float, float)
        """
        rho = math.sqrt(x ** 2 + y ** 2)
        phi = math.atan2(y, x)
        return (phi, rho)

    async def reset(self, seat):
        """Joystick reset functionality

        Defaults to x=0, y=0

        :param seat: Robot seat
        :type seat: int
        """
        await self.handle_coordinates(0, 0, seat)

    def get_name(self):
        """Returns the name of the input

        :return: name of the input
        :rtype: str
        """
        return "joystick"

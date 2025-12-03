from enum import Enum

class McpNpConstant(Enum):
    PI = "PI"
    E = "E"
    SPEED_OF_LIGHT = "speed_of_light"
    PLANCK = "planck"
    ELEMENTARY_CHARGE = "elementary_charge"
    GRAVITATIONAL_CONSTANT = "gravitational_constant"
    ELECTRON_MASS = "electron_mass"
    PROTON_MASS = "proton_mass"

    def __str__(self):
        return self.value
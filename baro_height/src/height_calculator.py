import math

class BaroHeightCalculator:
    """
    Calculates relative height offset based on pressure and temperature measurements.
    Uses the hypsometric equation.
    """

    # Physical constants
    R = 8.3144598  # Universal gas constant [J/(mol K)]
    g = 9.80665    # Gravity [m/s^2]
    M = 0.0289644  # Molar mass of Earth's air [kg/mol]

    def __init__(self, scale: float = 1.0):
        """
        Initialize the calculator.

        Args:
            scale: Calibration scale factor (default 1.0).
                   According to experiments, this might need to be ~1.25.
        """
        self.p_ref = None
        self.scale = scale
        self.zero_offset = 0.0 # Used if we want to reset 0 to a non-zero value or just shift

    def reset_zero(self, pressure: float, temperature: float, current_height: float = 0.0):
        """
        Set the current pressure and temperature as the reference level (0 height or specified height).

        Args:
            pressure: Current pressure in Pascals.
            temperature: Current temperature in Celsius.
            current_height: The height to assign to this pressure/temperature (default 0.0).
        """
        self.p_ref = pressure
        # We could store t_ref, but the formula usually uses the T at the point of measurement
        # or the average T. For relative short heights, using current T is fine.
        # But for stability, maybe we should use the T at reset?
        # The design doc says: Delta h = (R T / M g) * ln(p_ref / p)
        # We will use the average of T at reset and current T for better accuracy if available,
        # otherwise just current T. Let's store T_ref just in case.
        self.t_ref_k = temperature + 273.15

        # If we want the output to be `current_height` at this point.
        # h_rel = calculated_h + offset
        # calculated_h is 0 at this point.
        # so offset = current_height
        self.zero_offset = current_height

    def set_calibration(self, scale: float):
        """
        Set the calibration scale factor.

        Args:
            scale: The scale factor to apply to the calculated height difference.
        """
        self.scale = scale

    def calculate_height(self, pressure: float, temperature: float) -> float:
        """
        Calculate relative height.

        Args:
            pressure: Current pressure in Pascals.
            temperature: Current temperature in Celsius.

        Returns:
            Relative height in meters.
            Returns 0.0 if reset_zero has not been called.
        """
        if self.p_ref is None:
            return 0.0

        t_k = temperature + 273.15

        # Use average temperature for better accuracy over larger ranges
        # T_avg = (T_current + T_ref) / 2
        t_avg = (t_k + self.t_ref_k) / 2.0

        # Hypsometric equation
        # h = (R * T_avg) / (M * g) * ln(p_ref / p)

        # Avoid division by zero or log of zero/negative (unlikely for proper pressure)
        if pressure <= 0:
            return 0.0

        term = (self.R * t_avg) / (self.M * self.g)
        h_raw = term * math.log(self.p_ref / pressure)

        h_cal = h_raw * self.scale

        return h_cal + self.zero_offset

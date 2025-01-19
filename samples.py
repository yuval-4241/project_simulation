import  random
import math
import matplotlib.pyplot as plt

def f_SPA(x):
    if 0.5 <= x < 0.75:
        return 16 * (x - 0.5)
    elif 0.75 <= x <= 1:
        return 16 * (1 - x)
    else:
        return 0

def sample_spa():
    calls = 0
    while True:
        y = random.uniform(0.5, 1)  # במקום random.random()
  # הצעה מ-U(0,1)
        u = random.random()   # ציר Y: U(0, מקסימום של f(x))
        calls += 2
        if u <= f_SPA(y)/4:
            return y*60


def sampleSpa():
    """
    sample the time spent at the pool
    """
    u = np.random.uniform()
    if 0 < u <= 0.5:
        x = 1/2 + math.sqrt(2 * u) / 4
    elif 0.5 < u <= 1:
        x = -5 + ((640 * u + 281) ** 0.5)
    return x



def samplePoolSpent():
    """
    sample the time spent at the pool
    """
    u = np.random.uniform()
    if 0 < u <= 0.25:
        x = ((12 * u) + 1) ** 0.5
    elif 0.25 < u <= 0.875:
        x = -5 + ((640 * u + 281) ** 0.5)
    else:
        x = 8 * u - 4
    return x



import math
import numpy as np

def boxMuller(mean, variance):
    """
    Generate a single sample from a normal distribution using the Box-Muller transform.
    """
    # Calculate the standard deviation (σ) from the variance
    std_dev = np.sqrt(variance)

    # Generate two uniform random numbers in the range [0, 1) using NumPy
    u1, u2 = np.random.uniform(0, 1, 2)

    # Apply the Box-Muller transformation to generate one standard normal variable
    z1 = np.sqrt(-2 * np.log(u1)) * np.cos(2 * np.pi * u2)

    # Scale and shift the result to match the desired mean and variance
    sample = max(0, mean + z1 * std_dev)  # Ensure the sample is non-negative

    return sample

def sampleExponential(lambda_val):
    """
    Generate a single sample from an exponential distribution.
    """

    u = random.random()
    return -math.log(1 - u) / lambda_val

def sampleStayDuration ():
    """
    Generate a random sample for stay duration.
    """
    u = random.random()
    if u <= 0.25:  # 0 עד 0.25
        return 1
    elif u <= 0.25 + 0.46:  # 0.25 עד 0.71
        return 2
    elif u <= 0.25 + 0.46 + 0.2:  # 0.71 עד 0.91
        return 3
    elif u <= 0.25 + 0.46 + 0.2 + 0.05:  # 0.91 עד 0.96
        return 4
    else:  # 0.96 עד 1
        return 5

def sampleCheckIn():
    """
    Generate a single Check-In sample using an exponential distribution.
    """
    lambda_checkin = 0.13751104800611477  # The check in lambda value obtained earlier
    return sampleExponential(lambda_checkin)

def sampleCheckOut():
    """
    Generate a single Check-Out sample using an exponential distribution.
    """
    lambda_checkout = 0.20346735189307463  # The check in lambda value obtained earlier
    return sampleExponential(lambda_checkout)

def sampleCustomerCount():
    """
    Sample the number of customers in a reservation.
    """
    u = random.random()
    if u <= 0.08 :
      return 4
    elif u >  0.08 and u <= 0.2 :
      return 3
    elif u > 0.2 and u <= 0.4 :
      return 5
    elif u > 0.4 and u <= 0.8 :
      return 2
    else:
       return 1

def sampleIsSuite(number_of_guests):
    """
    Determine if the reservation is for a suite (10% chance) only if the number of guests is less than or equal to 2.
    Returns: bool: True if it's a suite (10% chance for <= 2 guests), False otherwise.
    """
    if number_of_guests <= 2:  # Only singles or couples can get a suite in 10% chance
        u = random.random()
        return u <= 0.1
    return False

def sampleBarService():
    """
    Generate a single sample for Bar Service time.
    """
    return boxMuller(5, 1.5)

def sampleBreakfastTime():
    """
    Generate a single sample for Breakfast time.
    """
    return round(boxMuller(40, 100))

def sampleBreakfastRate():
    """
    Generate a single Check-In sample using an exponential distribution.
    """
    lambda_breakfast = 0.25 # The check in lambda value obtained earlier
    return sampleExponential(lambda_breakfast)



def sampleCustomerArrival(hotel, H=7, R_available=120):
    """
    Generate a time for the next customer arrival based on the hotel's current state.
    """
    ALPHA = 20
    BETA1 = 1.5
    BETA2 = 2
    TOTAL_ROOMS = 110

    # Calculate hotel metrics
    H = 7  # דירוג ממוצע
    R_available = 110 # חדרים פנויים

    # Compute lambda
    lambda_value = ALPHA * ((R_available / TOTAL_ROOMS) ** BETA1) * ((H / 10) ** BETA2)

    # Sample the inter-arrival time
    return np.random.exponential(1 / lambda_value) if lambda_value > 0 else float('inf')

def sampleCustomerArrival(lambda_val):
    """
    Generate a time for the next customer arrival based on the hotel's current state.
    """
    if lambda_val is None or lambda_val == 0:
      return float('inf')  # אם אין לקוחות מגיעים, זמן ההגעה הבא הוא אינסופי
    return sampleExponential(lambda_val)
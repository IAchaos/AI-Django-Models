# This file used to contain pure computations that takes input
# and returns output with no dependency on self or the database.

import math
from django.utils import timezone


# Function 1 : format_salary
def format_salary(salary_min, salary_max):
    """
    Takes two integers — both optional — and returns a human readable string.
    :param salary_min: int
    :param salary_max: int
    :return: String formated_salary
    """


    if salary_min is None and salary_max is None:
        return "Salary not disclosed"

    elif salary_min is not None and salary_max is None:
        return f"From ${salary_min:,}"

    elif salary_max is not None and salary_min is None:
        return f"Up to ${salary_max:,}"
    else:
        return f"${salary_min:,} - ${salary_max:,}"



# Function 2 - calculate_reading_time(text)

def calculate_reading_time(text):
    words_count = len(text.split())


    minutes = max(1,math.ceil(words_count / 200))
    return f"{minutes} min read"

# Function 3 - days_until_expiry(expires_at)
def days_until_expiry(expires_at):
    if expires_at < timezone.now():
        return 0
    else:
        return (expires_at - timezone.now()).days


# Function 4 - is_salary_competitive(salary_max, threshold=80000)
def is_salary_competitive(salary_max, threshold=80000):
    if salary_max is None:
        return False
    return salary_max > threshold










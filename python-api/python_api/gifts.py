import random
import string


def generate_invitation_code():
    # Use only uppercase letters
    characters = string.ascii_uppercase
    # Generate two 4-character parts
    part1 = "".join(random.choice(characters) for _ in range(4))
    part2 = "".join(random.choice(characters) for _ in range(4))
    # Join the parts with a dash in the middle
    return f"{part1}-{part2}"

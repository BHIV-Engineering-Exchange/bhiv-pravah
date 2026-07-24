def calculate_reward(priority_score):

    if priority_score > 0.8:
        return 10

    elif priority_score > 0.5:
        return 5

    return 1
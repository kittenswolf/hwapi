# -*- coding: utf-8 -*-

def average_rating(weighted_rating, num_votes):
    a = 10
    b = 2.5

    if num_votes == 0:
        c = 0
    else:
        c = (weighted_rating - b * a / (num_votes + a)) / (num_votes / (num_votes + a))

    return round(min(5, max(c, 0)), 2)

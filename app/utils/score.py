def setScore(sim, dist_m, alpha=0.7, scale_m=5000.0) -> float:
    import math
    return alpha*sim + (1-alpha)*math.exp(-(dist_m/scale_m))
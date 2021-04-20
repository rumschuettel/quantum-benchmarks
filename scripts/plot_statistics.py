import numpy as np
import matplotlib.pyplot as plt

ps_scores, ps_errors = [], []
s_scores, s_errors = [], []
with open("statistics.txt") as f:
    for line in f:
        if line.startswith("Post-selection"):
            score, error = map(float, line.split(": ")[1].strip(".\n").split("±"))
            ps_scores.append(score)
            ps_errors.append(error)
        elif line.startswith("Success"):
            score, error = map(float, line.split(": ")[1].strip(".\n").split("±"))
            s_scores.append(score)
            s_errors.append(error)

fig = plt.figure()
ax = fig.gca()
ax.hist(ps_scores)
mean_score = np.mean(ps_scores)
mean_error_estimate = np.mean(ps_errors)
ax.plot([mean_score - mean_error_estimate] * 2, [0, 10], color="k", linestyle="--")
ax.plot([mean_score + mean_error_estimate] * 2, [0, 10], color="k", linestyle="--")
ax.set_title("Post-selection probability score")
ax.set_xlabel("Score")
ax.set_ylabel("Frequency")

fig = plt.figure()
ax = fig.gca()
ax.hist(s_scores)
mean_score = np.mean(s_scores)
mean_error_estimate = np.mean(s_errors)
ax.plot([mean_score - mean_error_estimate] * 2, [0, 10], color="k", linestyle="--")
ax.plot([mean_score + mean_error_estimate] * 2, [0, 10], color="k", linestyle="--")
ax.set_title("Success probability score")
ax.set_xlabel("Score")
ax.set_ylabel("Frequency")

plt.show()

import matplotlib.pyplot as plt
import itertools as it
from experiment import run_experiment_fill_axes

num_pixels = 64
post_selections = [1,2,3]
runs = [float("Inf"),2**5,2**10]

h = len(runs)
w = len(post_selections)

fig = plt.figure(figsize = (12,8))
for i,(num_runs,num_post_selections) in enumerate(it.product(runs, post_selections)):
    ax_psps = fig.add_subplot(h,2*w,2*i+1)
    ax_zs = fig.add_subplot(h,2*w,2*i+2)
    run_experiment_fill_axes(ax_psps, ax_zs, num_post_selections, num_pixels, num_runs)
plt.show()
